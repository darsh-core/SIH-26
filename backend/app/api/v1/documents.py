import os
import uuid
import shutil
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.core.config import settings
from app.models.user import AppUser
from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.models.assessment import Assessment, Question, QuestionOption, QuestionCompetency
from app.services.document_processing_service import DocumentProcessingService
from app.ai.competency_mapper import CompetencyMapper
from app.ai.mcq_generator import MCQGenerator
from app.schemas.assessment import GenerationRequest, GenerationResponse, GeneratedMCQ
from app.ai import get_embedding_provider, get_llm_provider

router = APIRouter(prefix="/documents", tags=["Document Management & AI RAG"])

# Constants
UPLOAD_DIR = "/Users/darshini/.gemini/antigravity-ide/scratch/sih-competency-platform/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class GenerateAssessmentRequest(BaseModel):
    competency_id: uuid.UUID
    question_count: int = 5
    difficulty: str = "MEDIUM"

class QuestionReviewRequest(BaseModel):
    action: Optional[str] = None  # "APPROVE" or "REJECT"
    status: Optional[str] = None
    feedback: Optional[str] = None
    review_notes: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED, summary="Upload Document")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Enforce authenticated official/trainer permission for uploads
    user_roles = [r.name for r in current_user.roles]
    if not (current_user.is_superuser or any(r in ["ADMIN", "ADMINISTRATOR", "TRAINER", "SUPERVISOR", "MANAGER", "EVALUATOR"] for r in user_roles)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized personnel can upload files")

    # 1. File verification
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Read contents and calculate SHA-256 for deduplication
    try:
        file.file.seek(0)
        contents = file.file.read()
        size = len(contents)
            
        if size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit")
            
        file_sha256 = hashlib.sha256(contents).hexdigest()

        # Check duplicate
        existing_doc = db.query(Document).filter(Document.checksum == file_sha256).first()
        if existing_doc:
            chunk_count = db.query(DocumentChunk).filter_by(document_id=existing_doc.id).count()
            return {
                "document_id": existing_doc.id,
                "title": existing_doc.title,
                "filename": existing_doc.filename,
                "status": existing_doc.status,
                "size_bytes": existing_doc.file_size_bytes,
                "is_duplicate": True,
                "chunk_count": chunk_count,
                "message": f"Document already exists (SHA-256: {file_sha256[:8]}...) with status '{existing_doc.status}'."
            }

        # Save to disk
        file_id = uuid.uuid4()
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
        with open(save_path, "wb") as buffer:
            buffer.write(contents)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # 3. Persist Document metadata
    db_doc = Document(
        id=file_id,
        title=os.path.splitext(filename)[0].replace("_", " ").replace("-", " "),
        filename=filename,
        file_type=ext.replace(".", "").upper(),
        file_path=save_path,
        file_size_bytes=size,
        status="UPLOADED",
        checksum=file_sha256,
        mime_type=file.content_type,
        uploaded_by=current_user.id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 4. Trigger processing in background task
    background_tasks.add_task(DocumentProcessingService.process_document, db, db_doc.id)

    return {
        "document_id": db_doc.id,
        "title": db_doc.title,
        "filename": db_doc.filename,
        "status": db_doc.status,
        "size_bytes": db_doc.file_size_bytes,
        "is_duplicate": False,
        "message": "Document uploaded successfully. Background extraction & indexing started."
    }


@router.get("", summary="List Documents")
def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    offset = (page - 1) * size
    total = db.query(Document).count()
    items = db.query(Document).order_by(Document.created_at.desc()).offset(offset).limit(size).all()
    
    docs_payload = []
    for doc in items:
        chunk_count = db.query(DocumentChunk).filter_by(document_id=doc.id).count()
        docs_payload.append({
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "status": doc.status,
            "chunk_count": chunk_count,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
        })
        
    return {
        "items": docs_payload,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{id}", summary="Get Document Details")
def get_document(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunk_count = db.query(DocumentChunk).filter_by(document_id=doc.id).count()
    
    # Extract sample text content to map competencies
    sample_chunks = db.query(DocumentChunk).filter_by(document_id=doc.id).limit(3).all()
    sample_text = " ".join([c.text_content for c in sample_chunks])
    
    detected_competencies = []
    if sample_text:
        detected_competencies = CompetencyMapper.map_document_to_competencies(db, sample_text)
        
    return {
        "id": doc.id,
        "title": doc.title,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "status": doc.status,
        "chunk_count": chunk_count,
        "detected_competencies": detected_competencies,
        "metadata": doc.metadata_json
    }


@router.post("/search", summary="RAG Similarity Search Debugger")
def rag_search(
    request: RAGSearchRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    provider = get_embedding_provider()
    query_vector = provider.embed_text(request.query)
    
    similar = DocumentProcessingService.search_similar_chunks(db, query_vector, request.top_k)
    
    results = []
    for chunk, similarity in similar:
        meta = chunk.metadata_json or {}
        results.append({
            "chunk_id": chunk.id,
            "document": chunk.document.title,
            "page": chunk.page_number if meta.get("source_type") != "slide" else None,
            "slide": chunk.page_number if meta.get("source_type") == "slide" else None,
            "similarity": round(similarity, 3),
            "text": chunk.text_content
        })
        
    return {"results": results}


@router.post("/{id}/generate-mcqs", response_model=GenerationResponse, summary="Generate Grounded MCQs")
def generate_mcqs(
    id: uuid.UUID,
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    user_roles = [r.name for r in current_user.roles]
    if not (current_user.is_superuser or any(r in ["ADMIN", "ADMINISTRATOR", "TRAINER", "EVALUATOR", "OFFICIAL", "SUPERVISOR", "MANAGER"] for r in user_roles)):
        raise HTTPException(status_code=403, detail="Only authorized personnel can generate questions")
        
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        response_payload = MCQGenerator.generate_grounded_mcqs(
            db=db,
            document_id=id,
            competency_id=request.competency_id,
            difficulty=request.difficulty,
            count=request.count
        )
        return response_payload
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/generate-assessment", summary="Create RAG-Grounded Assessment")
def generate_assessment(
    id: uuid.UUID,
    request: GenerateAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    user_roles = [r.name for r in current_user.roles]
    if not (current_user.is_superuser or any(r in ["ADMIN", "ADMINISTRATOR", "TRAINER", "EVALUATOR", "OFFICIAL", "SUPERVISOR", "MANAGER"] for r in user_roles)):
        raise HTTPException(status_code=403, detail="Only authorized personnel can publish assessments")
        
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # 1. Generate grounded questions
    res = MCQGenerator.generate_grounded_mcqs(
        db=db,
        document_id=id,
        competency_id=request.competency_id,
        difficulty=request.difficulty,
        count=request.question_count
    )
    
    valid_mcqs: List[GeneratedMCQ] = res["questions"]
    if not valid_mcqs:
        raise HTTPException(status_code=400, detail="No valid questions could be generated from the document context")
        
    # 2. Create Assessment Instance
    if settings.AI_PROVIDER == "groq":
        active_model = settings.GROQ_MODEL
    elif settings.AI_PROVIDER == "ollama":
        active_model = settings.OLLAMA_MODEL
    else:
        active_model = "mock-statistical-llm"
    assessment = Assessment(
        title=f"AI Grounded Evaluation: {doc.title}",
        description=f"Automated evaluation grounded in official publication '{doc.title}'. Target competency: {res['competency']}.",
        time_limit_minutes=20,
        pass_percentage=60.0,
        is_ai_generated=True
    )
    db.add(assessment)
    db.flush()
    
    # 3. Persist individual questions and link competencies with full source traceability
    for mcq in valid_mcqs:
        source_chunk_id = mcq.source_chunk_ids[0] if mcq.source_chunk_ids else None
        q = Question(
            assessment_id=assessment.id,
            text=mcq.question,
            question_type="MCQ",
            difficulty=mcq.difficulty,
            explanation=mcq.explanation,
            confidence=mcq.confidence,
            source_doc_id=id,
            source_page=mcq.source_page,
            source_chunk_id=source_chunk_id,
            generation_method="rag-grounded-v1",
            ai_model=active_model,
            grounding_score=mcq.grounding_score,
            metadata_json={
                "source_chunk_ids": [str(cid) for cid in mcq.source_chunk_ids],
                "review_status": "PENDING_REVIEW",
                "created_at": datetime.now().isoformat()
            }
        )
        db.add(q)
        db.flush()
        
        # Options persistence
        for opt in mcq.options:
            is_correct = (mcq.options.index(opt) == mcq.correct_answer)
            db_opt = QuestionOption(
                question_id=q.id,
                text=opt.text,
                is_correct=is_correct
            )
            db.add(db_opt)
            
        # Map competencies
        db_qc = QuestionCompetency(
            question_id=q.id,
            competency_id=request.competency_id,
            target_level=3,
            weight=1.0
        )
        db.add(db_qc)
        
    db.commit()
    db.refresh(assessment)
    
    return {
        "assessment_id": assessment.id,
        "title": assessment.title,
        "question_count": len(valid_mcqs),
        "competency": res["competency"],
        "difficulty": request.difficulty,
        "review_status": "PENDING_REVIEW"
    }


@router.put("/questions/{question_id}/review", summary="Trainer Question Approval Workflow")
def review_question(
    question_id: uuid.UUID,
    request: QuestionReviewRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    """Allows trainers and evaluators to inspect source traceability and approve or reject AI-generated questions."""
    user_roles = [r.name for r in current_user.roles]
    if not (current_user.is_superuser or any(r in ["ADMIN", "ADMINISTRATOR", "TRAINER", "EVALUATOR"] for r in user_roles)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators/evaluators can review questions")

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    action_raw = (request.action or request.status or "").upper()
    if action_raw in ["APPROVED", "APPROVE"]:
        action = "APPROVE"
    elif action_raw in ["REJECTED", "REJECT"]:
        action = "REJECT"
    else:
        raise HTTPException(status_code=400, detail="Action must be either APPROVE or REJECT")

    meta = dict(q.metadata_json or {})
    meta["review_status"] = "APPROVED" if action == "APPROVE" else "REJECTED"
    meta["reviewed_by"] = str(current_user.id)
    meta["reviewed_at"] = datetime.now().isoformat()
    feedback = request.feedback or request.review_notes
    if feedback:
        meta["review_feedback"] = feedback

    q.metadata_json = meta
    db.commit()

    return {
        "question_id": q.id,
        "review_status": meta["review_status"],
        "reviewed_by": current_user.email,
        "message": f"Question has been successfully {meta['review_status'].lower()}."
    }

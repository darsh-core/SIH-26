import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_authenticated_user
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
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class GenerateAssessmentRequest(BaseModel):
    competency_id: uuid.UUID
    question_count: int = 5
    difficulty: str = "MEDIUM"

@router.post("", status_code=status.HTTP_201_CREATED, summary="Upload Document")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Enforce admin permission for uploads
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can upload files")

    # 1. File verification
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save to temp path to verify sizes
    file_id = uuid.uuid4()
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    try:
        file.file.seek(0)
        contents = file.file.read()
        with open(save_path, "wb") as buffer:
            buffer.write(contents)
        size = len(contents)
            
        if size == 0:
            os.remove(save_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if size > MAX_FILE_SIZE:
            os.remove(save_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit")
            
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # 2. Persist Document metadata
    db_doc = Document(
        id=file_id,
        title=os.path.splitext(filename)[0].replace("_", " ").replace("-", " "),
        filename=filename,
        file_type=ext.replace(".", "").upper(),
        file_path=save_path,
        file_size_bytes=size,
        status="UPLOADED",
        mime_type=file.content_type,
        uploaded_by=current_user.id
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 3. Trigger processing in background task
    background_tasks.add_task(DocumentProcessingService.process_document, db, db_doc.id)

    return {
        "document_id": db_doc.id,
        "title": db_doc.title,
        "filename": db_doc.filename,
        "status": db_doc.status,
        "size_bytes": db_doc.file_size_bytes
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
        results.append({
            "chunk_id": chunk.id,
            "document": chunk.document.title,
            "page": chunk.page_number,
            "similarity": round(similarity, 3),
            "text": chunk.text_content
        })
        
    return {"results": results}


@router.post("/{id}/generate-mcqs", response_model=GenerationResponse, summary="Generate MCQs")
def generate_mcqs(
    id: uuid.UUID,
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Enforce admin privilege check
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only administrators can generate questions")
        
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Generate questions via retrieval loop
    response_payload = MCQGenerator.generate_grounded_mcqs(
        db=db,
        document_id=id,
        competency_id=request.competency_id,
        difficulty=request.difficulty,
        count=request.count
    )
    
    return response_payload


@router.post("/{id}/generate-assessment", summary="Create RAG-Grounded Assessment")
def generate_assessment(
    id: uuid.UUID,
    request: GenerateAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only administrators can publish assessments")
        
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
    assessment = Assessment(
        title=f"AI Generated Checkpoint: {doc.title}",
        description=f"Automated evaluation grounded in source manual '{doc.title}'. Target competency: {res['competency']}.",
        time_limit_minutes=20,
        pass_percentage=60.0,
        is_ai_generated=True
    )
    db.add(assessment)
    db.flush()
    
    # 3. Persist individual questions and link competencies
    for mcq in valid_mcqs:
        q = Question(
            assessment_id=assessment.id,
            text=mcq.question,
            question_type="MCQ",
            difficulty=mcq.difficulty,
            explanation=mcq.explanation,
            confidence=mcq.confidence,
            source_doc_id=id,
            source_page=mcq.source_page,
            source_chunk_id=mcq.source_chunk_ids[0] if mcq.source_chunk_ids else None,
            generation_method="mcq-v1",
            ai_model="mock-llm",
            grounding_score=mcq.grounding_score,
            metadata_json={
                "source_chunk_ids": [str(cid) for cid in mcq.source_chunk_ids]
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
            target_level=3, # default evaluation target
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
        "difficulty": request.difficulty
    }

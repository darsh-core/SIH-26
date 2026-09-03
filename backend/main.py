import time
import json
import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import SessionLocal, User, Role, Skill, RoleSkill, UserSkill, Course, AssessmentSession, AssessmentQuestion, Document, DocumentState
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ai.assessment_generator import AssessmentGenerator
from services.document_service import DocumentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SkillStat AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Schemas ---
class UserCreate(BaseModel):
    name: str
    department: str
    experience_years: int
    role_id: int

class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: int

class AssessmentSubmit(BaseModel):
    session_id: int
    answers: List[AnswerSubmit]

# --- Helper Methods ---
def calculate_skill_level(earned_points: int, max_points: int) -> int:
    if max_points == 0:
        return 1
    percentage = (earned_points / max_points) * 100
    if percentage <= 20:
        return 1
    elif percentage <= 40:
        return 2
    elif percentage <= 60:
        return 3
    elif percentage <= 80:
        return 4
    else:
        return 5

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"status": "SkillStat AI Backend is running"}

@app.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return [{"id": r.id, "name": r.name} for r in roles]

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == user.role_id).all()
    for rs in role_skills:
        db_us = UserSkill(user_id=db_user.id, skill_id=rs.skill_id, current_level=1)
        db.add(db_us)
    db.commit()
    
    return {"id": db_user.id, "name": db_user.name, "role_id": db_user.role_id}

@app.get("/users/{user_id}/assessment")
def generate_assessment(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == user.role_id).all()
    
    required_skills_info = []
    for rs in role_skills:
        s = db.query(Skill).filter(Skill.id == rs.skill_id).first()
        required_skills_info.append({
            "skill": s.name,
            "required_level": rs.required_level
        })
    
    generator = AssessmentGenerator()
    generation_result = generator.generate_assessment(user_id, user.role_id, role.name, required_skills_info)
    generated_qs = generation_result["questions"]
    generation_mode = generation_result["mode"]
    
    # Create persistent session
    db_session = AssessmentSession(
        user_id=user_id,
        role_id=user.role_id,
        status="pending",
        generation_mode=generation_mode,
        created_at=int(time.time())
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Save questions
    for gq in generated_qs:
        db_q = AssessmentQuestion(
            session_id=db_session.id,
            skill=gq["skill"],
            difficulty=gq["difficulty"],
            question=gq["question"],
            options=json.dumps(gq["options"]),
            correct_answer=gq["correct_answer"],
            explanation=gq["explanation"]
        )
        db.add(db_q)
    db.commit()
    
    # Fetch questions back to return safely
    persisted_qs = db.query(AssessmentQuestion).filter(AssessmentQuestion.session_id == db_session.id).all()
    
    clean_questions = []
    for q in persisted_qs:
        clean_questions.append({
            "id": q.id,
            "skill": q.skill,
            "difficulty": q.difficulty,
            "question": q.question,
            "options": json.loads(q.options)
        })
        
    return {
        "session_id": db_session.id,
        "generation_mode": generation_mode,
        "questions": clean_questions
    }

@app.post("/users/{user_id}/assessment/submit")
def submit_assessment(user_id: int, submission: AssessmentSubmit, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check session ownership and validity
    db_session = db.query(AssessmentSession).filter(
        AssessmentSession.id == submission.session_id
    ).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Assessment session not found")
        
    if db_session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
        
    if db_session.status != "pending":
        raise HTTPException(status_code=400, detail="Session is already completed")
        
    # Prevent submitting an older session if a newer pending one exists
    # Find the most recently created pending session for this user
    latest_pending = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == user_id,
        AssessmentSession.status == "pending"
    ).order_by(AssessmentSession.id.desc()).first()
    
    if latest_pending and latest_pending.id != db_session.id:
         # Optionally, invalidate the old one
         db_session.status = "abandoned"
         db.commit()
         raise HTTPException(status_code=400, detail="Cannot submit an older session. A newer assessment is active.")

    # Load all questions for this session
    session_questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.session_id == db_session.id).all()
    question_map = {q.id: q for q in session_questions}

    if len(submission.answers) == 0:
        raise HTTPException(status_code=400, detail="Cannot submit empty assessment")

    skill_earned = {}
    skill_max = {}
    
    difficulty_weights = {"easy": 1, "medium": 2, "hard": 3}
    
    for answer in submission.answers:
        q = question_map.get(answer.question_id)
        if not q:
            raise HTTPException(status_code=400, detail=f"Invalid question ID {answer.question_id} for this session")
            
        if answer.selected_option < 0 or answer.selected_option > 3:
            raise HTTPException(status_code=400, detail=f"Invalid selected option index for question {answer.question_id}")
            
        skill_name = q.skill
        weight = difficulty_weights.get(q.difficulty, 1)
        
        if skill_name not in skill_max:
            skill_max[skill_name] = 0
            skill_earned[skill_name] = 0
            
        skill_max[skill_name] += weight
        if answer.selected_option == q.correct_answer:
            skill_earned[skill_name] += weight
            
    # Update UserSkill records
    skills = db.query(Skill).filter(Skill.name.in_(skill_max.keys())).all()
    skill_name_to_id = {s.name: s.id for s in skills}
    
    for skill_name, max_p in skill_max.items():
        earned_p = skill_earned[skill_name]
        new_level = calculate_skill_level(earned_p, max_p)
        score_percent = (earned_p / max_p) * 100 if max_p > 0 else 0
        
        skill_id = skill_name_to_id.get(skill_name)
        if not skill_id:
            continue
            
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id, 
            UserSkill.skill_id == skill_id
        ).first()
        
        if user_skill:
            user_skill.current_level = new_level
            user_skill.assessment_score = score_percent
        else:
            new_us = UserSkill(user_id=user_id, skill_id=skill_id, current_level=new_level, assessment_score=score_percent)
            db.add(new_us)
            
    # Close session
    db_session.status = "completed"
    db_session.completed_at = int(time.time())
    db.commit()
    
    return {"status": "success", "message": "Assessment scored and competencies updated"}

@app.get("/users/{user_id}/dashboard")
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == user.role_id).all()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    user_skill_map = {us.skill_id: us.current_level for us in user_skills}
    
    total_current_weighted = 0.0
    total_required_weighted = 0.0
    
    gaps = []
    for rs in role_skills:
        current = user_skill_map.get(rs.skill_id, 1) 
        gap_value = max(0, rs.required_level - current)
        gap_score = gap_value * rs.importance
        
        if gap_score >= 2.0:
            priority = "HIGH"
        elif gap_score >= 1.0:
            priority = "MEDIUM"
        elif gap_value > 0:
            priority = "LOW"
        else:
            priority = "GOOD_STANDING"
            
        total_current_weighted += (current * rs.importance)
        total_required_weighted += (rs.required_level * rs.importance)
        
        skill = db.query(Skill).filter(Skill.id == rs.skill_id).first()
        gaps.append({
            "skill_id": rs.skill_id,
            "skill": skill.name,
            "current_level": current,
            "required_level": rs.required_level,
            "gap_value": gap_value,
            "importance": rs.importance,
            "gap_score": round(gap_score, 2),
            "priority": priority
        })
        
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    
    overall_competency = 0.0
    if total_required_weighted > 0:
        overall_competency = round((total_current_weighted / total_required_weighted) * 100, 1)
    
    recommendations = []
    for gap in gaps[:3]:
        if gap["gap_value"] > 0:
            course = db.query(Course).filter(Course.target_skill_id == gap["skill_id"]).first()
            if course:
                recommendations.append({
                    "course_id": course.id,
                    "title": course.title,
                    "provider": course.provider,
                    "url": course.url,
                    "target_skill": gap["skill"],
                    "reason": f"Your role requires {gap['skill']} at Level {gap['required_level']}, but you are currently at Level {gap['current_level']}."
                })
                
    return {
        "user_name": user.name,
        "department": user.department,
        "overall_competency": overall_competency,
        "gaps": gaps,
        "recommendations": recommendations
    }

# ==========================================
# Document Intelligence Endpoints
# ==========================================

@app.post("/users/{user_id}/documents")
async def upload_document(
    user_id: int, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        doc = await DocumentService.process_upload(user_id, file, db)
        
        # If it's a newly uploaded document, trigger background extraction
        if doc.processing_status == "UPLOADED":
            background_tasks.add_task(DocumentService.extract_document_background, doc.id, db)
            
        return {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.processing_status,
            "created_at": doc.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")

@app.get("/users/{user_id}/documents")
def list_documents(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    docs = db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()
    
    return [
        {
            "id": d.id,
            "original_filename": d.original_filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "status": d.processing_status,
            "error": d.processing_error,
            "chunk_count": len(d.chunks),
            "created_at": d.created_at
        }
        for d in docs
    ]

@app.get("/users/{user_id}/documents/{doc_id}")
def get_document(user_id: int, doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.processing_status,
        "error": doc.processing_error,
        "chunk_count": len(doc.chunks),
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }

@app.post("/users/{user_id}/documents/{doc_id}/embed")
def trigger_embedding(user_id: int, doc_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.processing_status not in ["READY_FOR_EMBEDDING", "FAILED", "EMBEDDED"]:
        raise HTTPException(status_code=400, detail=f"Document is not ready for embedding. Current status: {doc.processing_status}")
        
    doc.processing_status = DocumentState.EMBEDDING.value
    doc.processing_error = None
    db.commit()
    
    background_tasks.add_task(DocumentService.embed_document_background, doc.id, user_id, db)
    
    return {"status": doc.processing_status, "message": "Embedding job started"}

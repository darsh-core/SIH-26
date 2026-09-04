import uuid
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.models.assessment import AssessmentAttempt, Question, QuestionOption
from app.services.assessment_service import AssessmentService
from app.schemas.assessment import (
    AssessmentResponse,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentResultResponse,
    QuestionResponse,
    OptionResponse
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.get("", response_model=PaginatedResponse[AssessmentResponse], summary="List Assessments")
def list_assessments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    skip = (page - 1) * size
    items, total = AssessmentService.get_assessments(db, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/{id}", response_model=AssessmentResponse, summary="Get Assessment Details")
def get_assessment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    assessment = AssessmentService.get_assessment(db, id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    return assessment


@router.post("/{id}/start", response_model=AssessmentStartResponse, summary="Start Assessment Attempt")
def start_assessment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    attempt = AssessmentService.start_attempt(db, assessment_id=id, user_id=current_user.id)
    
    # Load questions (with options, but hiding the correct flag)
    questions = db.query(Question).filter(Question.assessment_id == id).all()
    
    question_responses = []
    for q in questions:
        options = [OptionResponse.model_validate(opt) for opt in q.options]
        question_responses.append(
            QuestionResponse(
                id=q.id,
                text=q.text,
                question_type=q.question_type,
                options=options
            )
        )
        
    return AssessmentStartResponse(
        attempt_id=attempt.id,
        assessment_id=id,
        started_at=attempt.started_at,
        questions=question_responses
    )


@router.post("/{id}/submit", response_model=AssessmentResultResponse, summary="Submit Assessment Answers")
def submit_assessment(
    id: uuid.UUID,
    submission: AssessmentSubmitRequest,
    attempt_id: uuid.UUID = Query(..., description="The ID of the attempt being submitted"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Verify the attempt is for this assessment
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == attempt_id,
        AssessmentAttempt.assessment_id == id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt does not match the specified assessment"
        )
        
    return AssessmentService.submit_attempt(
        db, attempt_id=attempt_id, user_id=current_user.id, submission=submission
    )


@router.get("/{id}/results", response_model=AssessmentResultResponse, summary="Get Attempt Results")
def get_assessment_results(
    id: uuid.UUID,
    attempt_id: Optional[uuid.UUID] = Query(None, description="Optional attempt ID to view, otherwise fetches latest attempt"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    query = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.assessment_id == id,
        AssessmentAttempt.user_id == current_user.id
    )
    
    if attempt_id:
        attempt = query.filter(AssessmentAttempt.id == attempt_id).first()
    else:
        attempt = query.order_by(AssessmentAttempt.completed_at.desc()).first()
        
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed attempts found for this assessment"
        )
        
    # Standard format return. We'll reconstruct the response manually from database relations
    from app.schemas.assessment import AssessmentAttemptResponse, CompetencyPerformance
    
    attempt_res = AssessmentAttemptResponse.model_validate(attempt)
    
    # Reconstruct competency performances
    from app.models.assessment import AttemptAnswer, QuestionCompetency
    answers = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
    
    comp_perf = {}
    for ans in answers:
        q = ans.question
        q_comps = db.query(QuestionCompetency).filter(QuestionCompetency.question_id == q.id).all()
        for qc in q_comps:
            comp_id = qc.competency_id
            if comp_id not in comp_perf:
                comp_perf[comp_id] = {
                    "correct": 0,
                    "total": 0,
                    "competency": qc.competency
                }
            comp_perf[comp_id]["total"] += 1
            if ans.is_correct:
                comp_perf[comp_id]["correct"] += 1
                
    performances = []
    for comp_id, perf in comp_perf.items():
        score = (perf["correct"] / perf["total"]) * 100.0
        performances.append(
            CompetencyPerformance(
                competency_code=perf["competency"].code,
                competency_name=perf["competency"].name,
                score=round(score, 1),
                questions_answered=perf["total"],
                questions_correct=perf["correct"]
            )
        )
        
    return AssessmentResultResponse(
        attempt=attempt_res,
        score=attempt.score,
        is_passed=attempt.is_passed,
        competency_performances=performances
    )


class RoleDiagnosticRequest(BaseModel):
    job_role_id: uuid.UUID
    question_count: int = 10

@router.post("/role-diagnostic", summary="Generate AI Role Diagnostic Assessment")
def generate_role_diagnostic(
    request: RoleDiagnosticRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    """Generates an AI-assisted diagnostic checkpoint for a Job Role and its required competencies."""
    from app.ai.role_assessment_generator import RoleDiagnosticGenerator
    try:
        res = RoleDiagnosticGenerator.generate_role_assessment(
            db=db,
            job_role_id=request.job_role_id,
            total_questions=request.question_count
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

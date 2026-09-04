import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.integrations.learning_provider import get_learning_provider
from app.core.config import settings
from app.schemas.learning import (
    NormalizedLearningResource,
    CourseLaunchResponse,
    LearningEnrollmentResponse,
    LearningProgressDetailResponse,
    LearningHistoryItemResponse,
    ProviderInfoResponse,
)

router = APIRouter(prefix="/learning", tags=["Learning & iGOT Ecosystem"])


@router.get("/providers", response_model=List[ProviderInfoResponse], summary="List Active Learning Providers")
def list_providers(
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Returns information on integrated learning providers.
    Transparently marks Demo vs Live mode based on server configuration.
    """
    is_demo = settings.LEARNING_PROVIDER.lower().strip() != "igot"
    return [
        ProviderInfoResponse(
            code="igot",
            name="iGOT Karmayogi",
            provider_type="DEMO" if is_demo else "LIVE",
            description="Integrated Government Online Training platform for civil services capability building.",
            is_active=True,
            is_configured=not is_demo,
        ),
        ProviderInfoResponse(
            code="nssta",
            name="National Statistical Systems Training Academy (NSSTA)",
            provider_type="DEMO",
            description="Apex institute for official statistical training and professional capacity development.",
            is_active=True,
            is_configured=True,
        ),
    ]


@router.get("/courses", response_model=List[NormalizedLearningResource], summary="Search and List Learning Resources")
def search_courses(
    competency: Optional[str] = Query(None, description="Filter by competency code (e.g. STAT_SAMPLING)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Beginner, Intermediate, Advanced)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Search courses through the configured learning provider abstraction.
    """
    provider = get_learning_provider()
    comp_codes = [competency] if competency else None
    return provider.search_courses(
        db, competency_codes=comp_codes, difficulty=difficulty, skip=skip, limit=limit
    )


@router.get("/courses/{course_id}", response_model=NormalizedLearningResource, summary="Get Course Details with Modules")
def get_course_details(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Retrieve full course details including module and lesson breakdown.
    """
    provider = get_learning_provider()
    course = provider.get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_id}' not found.",
        )
    return course


@router.post("/courses/{course_id}/enroll", response_model=LearningEnrollmentResponse, summary="Enroll in Course")
def enroll_in_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Idempotently enroll the authenticated employee into a course.
    """
    provider = get_learning_provider()
    return provider.enroll(db, user_id=current_user.id, course_id_or_code=course_id)


@router.post("/courses/{course_id}/launch", response_model=CourseLaunchResponse, summary="Launch Course Player")
def launch_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Launches course learning session. Returns authorized launch route.
    For Demo mode, maps to SANKHYAI's demo player.
    """
    provider = get_learning_provider()
    return provider.launch_course(db, user_id=current_user.id, course_id_or_code=course_id)


@router.get("/courses/{course_id}/progress", response_model=LearningProgressDetailResponse, summary="Get Course Learning Progress")
def get_course_progress(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Retrieve module-by-module learning progress for the authenticated employee.
    """
    provider = get_learning_provider()
    return provider.get_progress(db, user_id=current_user.id, course_id_or_code=course_id)


@router.post("/courses/{course_id}/modules/{module_id}/complete", response_model=LearningProgressDetailResponse, summary="Complete Learning Module")
def complete_learning_module(
    course_id: str,
    module_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Mark an individual module as completed and recalculate overall progress percentage.
    """
    provider = get_learning_provider()
    return provider.complete_module(
        db, user_id=current_user.id, course_id_or_code=course_id, module_id_or_code=module_id
    )


@router.post("/courses/{course_id}/complete", response_model=LearningProgressDetailResponse, summary="Complete Entire Course")
def complete_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Mark all modules as completed and finalize course completion record.
    """
    provider = get_learning_provider()
    return provider.complete_course(db, user_id=current_user.id, course_id_or_code=course_id)


@router.get("/history", response_model=List[LearningHistoryItemResponse], summary="Get Employee Learning History")
def get_user_learning_history(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user),
):
    """
    Retrieve the authenticated employee's complete learning history of enrolled and completed courses.
    """
    provider = get_learning_provider()
    return provider.get_learning_history(db, user_id=current_user.id)

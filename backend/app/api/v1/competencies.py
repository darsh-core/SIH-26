import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.models.competency import Competency
from app.services.competency_service import CompetencyService
from app.schemas.competency import CompetencyResponse, CompetencyLevelResponse
from app.schemas.role import RoleResponse
from app.schemas.course import CourseResponse
from app.schemas.common import PaginatedResponse
from app.services.gap_engine import GapEngine
from app.schemas.recommendation import PersonalizedItemResponse, CompetencyGapDetail

router = APIRouter(tags=["Competencies"])

@router.get("/competencies", response_model=PaginatedResponse[CompetencyResponse], summary="List Competencies")
def list_competencies(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    framework: Optional[str] = Query(None, description="Filter by framework name (e.g. STATISTICAL, TECHNICAL)"),
    search: Optional[str] = Query(None, description="Search text in name or code"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    skip = (page - 1) * size
    items, total = CompetencyService.get_competencies(
        db, framework_name=framework, search=search, skip=skip, limit=size
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/competencies/gaps", response_model=List[CompetencyGapDetail], summary="Get Current User Competency Gaps")
def get_my_competency_gaps(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    gap_data = GapEngine.calculate_gaps(db, user_id=current_user.id)
    return gap_data.gaps


@router.get("/competencies/{id}", response_model=CompetencyResponse, summary="Get Competency Details")
def get_competency(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    comp = CompetencyService.get_competency(db, id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competency not found"
        )
    return comp


@router.get("/competencies/{id}/levels", response_model=List[CompetencyLevelResponse], summary="Get Competency Levels (1-5)")
def get_competency_levels(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    comp = CompetencyService.get_competency(db, id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competency not found"
        )
    return CompetencyService.get_competency_levels(db, id)


@router.get("/competencies/{id}/roles", response_model=List[RoleResponse], summary="Get Roles Requiring Competency")
def get_competency_roles(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    comp = CompetencyService.get_competency(db, id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competency not found"
        )
    return CompetencyService.get_competency_roles(db, id)


@router.get("/competencies/{id}/courses", response_model=List[CourseResponse], summary="Get Courses Mapped to Competency")
def get_competency_courses(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    comp = CompetencyService.get_competency(db, id)
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competency not found"
        )
    return CompetencyService.get_competency_courses(db, id)


@router.get("/users/{user_id}/competencies/{competency_id}/recommendations", response_model=List[PersonalizedItemResponse], summary="Get Competency-Specific Recommendations")
def get_competency_recommendations(
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Import here to prevent circular dependency
    from app.api.v1.recommendations import get_user_recommendations
    
    # Get all recommendations for the user
    resp = get_user_recommendations(
        user_id=user_id,
        priority=None,
        provider=None,
        competency=None,
        limit=10,
        debug=False,
        db=db,
        current_user=current_user
    )
    
    # Look up competency code
    comp = db.query(Competency).filter(Competency.id == competency_id).first()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competency not found"
        )
        
    # Filter items where target competency matches comp.code
    comp_recs = [
        item for item in resp.recommendations 
        if any(tc.code == comp.code for tc in item.target_competencies)
    ]
    
    return comp_recs

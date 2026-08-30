import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.services.course_service import CourseService
from app.schemas.course import CourseResponse, ProviderResponse, TrainingProgramResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/courses", tags=["Courses & Providers"])

@router.get("/providers", response_model=PaginatedResponse[ProviderResponse], summary="List Providers")
def list_providers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    skip = (page - 1) * size
    items, total = CourseService.get_providers(db, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("", response_model=PaginatedResponse[CourseResponse], summary="List Online Courses")
def list_courses(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    skip = (page - 1) * size
    items, total = CourseService.get_courses(db, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get("/training-programs", response_model=PaginatedResponse[TrainingProgramResponse], summary="List Training Programs")
def list_training_programs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    skip = (page - 1) * size
    items, total = CourseService.get_training_programs(db, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)

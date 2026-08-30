import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user, require_admin
from app.models.user import AppUser
from app.models.competency import JobRole, RoleCompetency
from app.schemas.role import RoleResponse, RoleCreate, RoleCompetencyResponse, RoleCompetencyDetail

router = APIRouter(prefix="/roles", tags=["Job Roles"])

@router.get("", response_model=List[RoleResponse], summary="List Job Roles")
def list_roles(db: Session = Depends(get_db), current_user: AppUser = Depends(require_authenticated_user)):
    return db.query(JobRole).all()


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create Job Role (Admin Only)")
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin())
):
    # Check if duplicate code or name
    role = db.query(JobRole).filter(JobRole.code == role_in.code).first()
    if role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job Role with code {role_in.code} already exists"
        )
    db_role = JobRole(**role_in.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@router.get("/{role_id}", response_model=RoleResponse, summary="Get Job Role Details")
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    role = db.query(JobRole).filter(JobRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job Role not found"
        )
    return role


@router.get("/{role_id}/competencies", response_model=RoleCompetencyResponse, summary="Get Required Competencies for Job Role")
def get_role_competencies(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    role = db.query(JobRole).filter(JobRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job Role not found"
        )
        
    mappings = db.query(RoleCompetency).filter(
        RoleCompetency.job_role_id == role_id
    ).all()
    
    comp_details = []
    for m in mappings:
        comp_details.append(
            RoleCompetencyDetail(
                code=m.competency.code,
                name=m.competency.name,
                required_level=m.required_level,
                weight=m.weight,
                mandatory=m.is_mandatory
            )
        )
        
    return RoleCompetencyResponse(role=role.name, competencies=comp_details)

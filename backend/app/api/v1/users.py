import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user, require_admin
from app.services.user_service import UserService
from app.services.competency_service import CompetencyService
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.schemas.competency import UserCompetencyResponse, EvidenceResponse, CompetencyUpdateRequest
from app.schemas.common import PaginatedResponse
from app.models.user import AppUser

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=PaginatedResponse[UserResponse], summary="List Users (Admin Only)")
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin())
):
    skip = (page - 1) * size
    users, total = UserService.get_users(db, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(items=users, total=total, page=page, size=size, pages=pages)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User (Admin Only)")
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin())
):
    return UserService.create_user(db, user_in)


@router.get("/{user_id}", response_model=UserResponse, summary="Get User Details")
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Only allow Admin or the User themselves
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot view details of other users"
        )
    user = UserService.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="Update User (Admin Only)")
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin())
):
    return UserService.update_user(db, user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete User (Admin Only)")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin())
):
    UserService.delete_user(db, user_id)


@router.get("/{user_id}/profile", response_model=ProfileResponse, summary="Get User Profile")
def get_user_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot view profiles of other users"
        )
    return UserService.get_profile(db, user_id)


@router.put("/{user_id}/profile", response_model=ProfileResponse, summary="Create or Update User Profile")
def update_user_profile(
    user_id: uuid.UUID,
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot update profiles of other users"
        )
    return UserService.create_or_update_profile(db, user_id, profile_in)


@router.get("/{user_id}/competencies", response_model=List[UserCompetencyResponse], summary="Get User Competency Levels")
def get_user_competencies(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        # Supervisors and Managers can also see user competencies, let's allow them
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: insufficient privileges"
            )
            
    user_comps = CompetencyService.get_user_competencies(db, user_id)
    
    # Map to schema containing details
    response = []
    for uc in user_comps:
        response.append(
            UserCompetencyResponse(
                id=uc.id,
                competency_id=uc.competency_id,
                competency_code=uc.competency.code,
                competency_name=uc.competency.name,
                current_level=uc.current_level,
                target_level=uc.target_level,
                status=uc.status,
                last_evaluated_at=uc.last_evaluated_at
            )
        )
    return response


@router.get("/{user_id}/evidence", response_model=List[EvidenceResponse], summary="Get User Competency Evidence Logs")
def get_user_evidence(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
    return CompetencyService.get_user_evidence(db, user_id)


@router.put("/{user_id}/competencies/{competency_id}", response_model=UserCompetencyResponse, summary="Update User Competency")
def update_user_competency(
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
    update_in: CompetencyUpdateRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot update other users' competencies"
            )
            
    verified_by = current_user.id if current_user.id != user_id else None
    
    uc = CompetencyService.update_user_competency(
        db, user_id=user_id, competency_id=competency_id, update_in=update_in, verified_by=verified_by
    )
    
    return UserCompetencyResponse(
        id=uc.id,
        competency_id=uc.competency_id,
        competency_code=uc.competency.code,
        competency_name=uc.competency.name,
        current_level=uc.current_level,
        target_level=uc.target_level,
        status=uc.status,
        last_evaluated_at=uc.last_evaluated_at
    )

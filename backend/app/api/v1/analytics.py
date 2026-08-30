import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.services.gap_engine import GapEngine
from app.schemas.recommendation import UserCompetencyGapsResponse

router = APIRouter(tags=["Analytics & Gap Engine"])

@router.get("/users/{user_id}/competency-gaps", response_model=UserCompetencyGapsResponse, summary="Get User Competency Gaps")
def get_user_competency_gaps(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Only allow Admin or Supervisor/Manager or User themselves
    if not current_user.is_superuser and current_user.id != user_id:
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot view competency gaps of other users"
            )
            
    return GapEngine.calculate_gaps(db, user_id=user_id)


@router.get("/users/{user_id}/readiness-score", summary="Get User Readiness Score Summary")
def get_user_readiness_score(
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
            
    return GapEngine.get_readiness_metrics(db, user_id=user_id)

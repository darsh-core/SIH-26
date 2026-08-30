import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser
from app.services.learning_plan_service import LearningPlanService
from app.schemas.learning_plan import LearningPlanResponse, LearningPlanCreate, LearningPlanItemResponse, LearningPlanItemAdd

router = APIRouter(tags=["Learning Plans"])

@router.post("/users/{user_id}/learning-plans/generate", response_model=LearningPlanResponse, status_code=status.HTTP_201_CREATED, summary="Auto-Generate Sequenced Learning Plan")
def generate_user_plan(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot generate plans for other users"
        )
    return LearningPlanService.generate_plan(db, user_id=user_id)


@router.get("/users/{user_id}/learning-plans", response_model=List[LearningPlanResponse], summary="List User Learning Plans")
def list_user_plans(
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
    return LearningPlanService.get_plans(db, user_id=user_id)


@router.get("/learning-plans/{plan_id}", response_model=LearningPlanResponse, summary="Get Learning Plan Details")
def get_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    plan = LearningPlanService.get_plan(db, plan_id=plan_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not found"
        )
    return plan


@router.post("/learning-plans/{plan_id}/items", response_model=LearningPlanItemResponse, status_code=status.HTTP_201_CREATED, summary="Add Item to Learning Plan")
def add_plan_item(
    plan_id: uuid.UUID,
    item_in: LearningPlanItemAdd,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    return LearningPlanService.add_plan_item(
        db, plan_id=plan_id, user_id=current_user.id, item_in=item_in
    )


@router.delete("/learning-plans/{plan_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove Item from Learning Plan")
def remove_plan_item(
    plan_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    LearningPlanService.delete_plan_item(db, plan_id=plan_id, user_id=current_user.id, item_id=item_id)


# Legacy Compatibility endpoint mapping /learning-plans to list current user's plans
@router.get("/learning-plans", response_model=List[LearningPlanResponse], summary="List Legacy Learning Plans")
def list_legacy_plans(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    return LearningPlanService.get_plans(db, user_id=current_user.id)

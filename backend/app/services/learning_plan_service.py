import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.recommendation import LearningPlan, LearningPlanItem
from app.schemas.learning_plan import LearningPlanCreate, LearningPlanItemAdd

class LearningPlanService:
    
    @staticmethod
    def get_plans(db: Session, user_id: uuid.UUID) -> List[LearningPlan]:
        return db.query(LearningPlan).filter(LearningPlan.user_id == user_id).all()

    @staticmethod
    def get_plan(db: Session, plan_id: uuid.UUID, user_id: uuid.UUID) -> Optional[LearningPlan]:
        return db.query(LearningPlan).filter(
            LearningPlan.id == plan_id,
            LearningPlan.user_id == user_id
        ).first()

    @staticmethod
    def create_plan(db: Session, user_id: uuid.UUID, plan_in: LearningPlanCreate) -> LearningPlan:
        plan = LearningPlan(
            user_id=user_id,
            title=plan_in.title,
            description=plan_in.description,
            status="ACTIVE",
            target_completion_date=plan_in.target_completion_date
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def add_plan_item(
        db: Session, plan_id: uuid.UUID, user_id: uuid.UUID, item_in: LearningPlanItemAdd
    ) -> LearningPlanItem:
        # Check plan ownership
        plan = LearningPlanService.get_plan(db, plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )

        # Build learning plan item
        item = LearningPlanItem(
            learning_plan_id=plan_id,
            item_type=item_in.item_type,
            course_id=item_in.course_id,
            training_program_id=item_in.training_program_id,
            sequence_order=item_in.sequence_order,
            status="PENDING"
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def generate_plan(db: Session, user_id: uuid.UUID) -> LearningPlan:
        # Import recommendation service here to avoid circular imports
        from app.services.recommendation_service import RecommendationService
        
        # 1. Fetch recommendations (generates if none)
        recs = RecommendationService.get_recommendations(db, user_id=user_id)
        
        # 2. Create the Learning Plan
        plan = LearningPlan(
            user_id=user_id,
            title="Personalized Skill Development Plan",
            description="Sequenced learning path auto-generated to close current competency gaps.",
            status="ACTIVE"
        )
        db.add(plan)
        db.flush()
        
        # 3. Add recommendations as items in sequence
        # Sequence order matches the recommendation score ranking
        for index, r in enumerate(recs):
            item = LearningPlanItem(
                learning_plan_id=plan.id,
                item_type=r.item_type,
                course_id=r.course_id,
                training_program_id=r.training_program_id,
                sequence_order=index + 1,
                status="PENDING",
                added_from_recommendation_id=r.id
            )
            db.add(item)
            
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def delete_plan_item(db: Session, plan_id: uuid.UUID, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        plan = LearningPlanService.get_plan(db, plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan not found"
            )
            
        item = db.query(LearningPlanItem).filter(
            LearningPlanItem.id == item_id,
            LearningPlanItem.learning_plan_id == plan_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning plan item not found"
            )
            
        db.delete(item)
        db.commit()

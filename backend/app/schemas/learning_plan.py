import uuid
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional, List

class LearningPlanItemResponse(BaseModel):
    id: uuid.UUID
    learning_plan_id: uuid.UUID
    item_type: str
    course_id: Optional[uuid.UUID] = None
    training_program_id: Optional[uuid.UUID] = None
    sequence_order: int
    status: str
    added_from_recommendation_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LearningPlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str
    target_completion_date: Optional[date] = None
    items: List[LearningPlanItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LearningPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_completion_date: Optional[date] = None

class LearningPlanItemAdd(BaseModel):
    item_type: str  # COURSE, TRAINING_PROGRAM
    course_id: Optional[uuid.UUID] = None
    training_program_id: Optional[uuid.UUID] = None
    sequence_order: int = 0

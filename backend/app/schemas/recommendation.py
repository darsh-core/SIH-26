import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class RecommendationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_type: str  # COURSE, TRAINING_PROGRAM
    course_id: Optional[uuid.UUID] = None
    training_program_id: Optional[uuid.UUID] = None
    competency_id: uuid.UUID
    gap_score: int
    recommendation_score: float
    logic_explanation: Optional[str] = None
    confidence_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class RoleInfo(BaseModel):
    code: str
    title: str

class CompetencyGapDetail(BaseModel):
    competency_code: str
    competency_name: str
    required_level: float
    current_level: float
    gap: float
    normalized_gap: float
    priority: str  # HIGH, MEDIUM, LOW, NONE
    priority_score: float = 0.0
    mandatory: bool
    weight: float

class UserCompetencyGapsResponse(BaseModel):
    user_id: uuid.UUID
    role: RoleInfo
    overall_readiness: float
    gaps: List[CompetencyGapDetail]


class TargetCompetencyDetail(BaseModel):
    code: str
    current_level: float
    required_level: float
    gap: float

class PersonalizedItemResponse(BaseModel):
    resource_id: uuid.UUID
    provider: str
    title: str
    resource_type: str  # COURSE, TRAINING_PROGRAM
    target_competencies: List[TargetCompetencyDetail]
    score: float
    priority: str  # HIGH, MEDIUM, LOW, NONE
    reason: str
    estimated_duration_minutes: int
    difficulty: str
    debug_scores: Optional[dict] = None

class PersonalizedRecommendationResponse(BaseModel):
    user_id: uuid.UUID
    role: str
    overall_readiness: float
    recommendations: List[PersonalizedItemResponse]

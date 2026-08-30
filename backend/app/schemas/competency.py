import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class CompetencyResponse(BaseModel):
    id: uuid.UUID
    framework_id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CompetencyLevelResponse(BaseModel):
    id: uuid.UUID
    competency_id: uuid.UUID
    level: int
    name: str
    description: str
    behavior_indicators: List[str]

    class Config:
        from_attributes = True

class UserCompetencyResponse(BaseModel):
    id: uuid.UUID
    competency_id: uuid.UUID
    competency_code: str
    competency_name: str
    current_level: float
    target_level: Optional[int] = None
    status: str
    last_evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CompetencyUpdateRequest(BaseModel):
    current_level: float = Field(..., ge=0.0, le=5.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., description="E.g. ASSESSMENT, CERTIFICATE, WORK_EVIDENCE")

class EvidenceResponse(BaseModel):
    id: uuid.UUID
    user_competency_id: uuid.UUID
    type: str
    source_id: Optional[uuid.UUID] = None
    description: str
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    metadata_json: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

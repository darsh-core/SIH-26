import uuid
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional, List

class ProviderResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

class CourseResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    difficulty: str
    language: str
    url: Optional[str] = None

    class Config:
        from_attributes = True

class TrainingProgramResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    duration_days: int
    location: Optional[str] = None
    mode: str
    eligibility_criteria: Optional[str] = None
    tpac_recommendation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True

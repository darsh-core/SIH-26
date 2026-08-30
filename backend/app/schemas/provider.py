from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class ProviderCompetencyMapping(BaseModel):
    competency_code: str
    target_level: int
    weight: float

class IGOTCourseDetail(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    difficulty: str
    language: str
    url: Optional[str] = None
    competency_mappings: List[ProviderCompetencyMapping]

class NSSTATrainingDetail(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    duration_days: int
    location: Optional[str] = None
    mode: str  # OFFLINE, ONLINE, HYBRID
    eligibility_criteria: Optional[str] = None
    tpac_recommendation: Optional[str] = None
    competency_mappings: List[ProviderCompetencyMapping]

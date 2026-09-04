import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class LearningCompetencyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    name: str
    target_level: int
    weight: float = 1.0


class LearningLessonDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    content: str
    duration_minutes: int
    sequence_order: int


class LearningModuleDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    sequence_order: int
    is_required: bool = True
    lessons: List[LearningLessonDetail] = []


class NormalizedLearningResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    provider: str  # "igot" or "nssta"
    provider_name: str  # "iGOT Karmayogi"
    external_course_id: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    difficulty: str  # "Beginner", "Intermediate", "Advanced"
    language: str = "English"
    course_url: Optional[str] = None
    is_demo: bool = True
    competencies: List[LearningCompetencyDetail] = []
    modules: List[LearningModuleDetail] = []
    metadata_json: Optional[Dict[str, Any]] = None


class ModuleProgressStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    module_id: uuid.UUID
    module_code: str
    module_title: str
    sequence_order: int
    status: str  # "NOT_STARTED", "IN_PROGRESS", "COMPLETED"
    completed_at: Optional[datetime] = None


class LearningProgressDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    external_course_id: str
    course_title: str
    provider_name: str = "iGOT Karmayogi"
    is_demo: bool = True
    progress_percentage: float
    status: str  # "ENROLLED", "IN_PROGRESS", "COMPLETED"
    completed_modules: int
    total_modules: int
    modules: List[ModuleProgressStatus] = []
    enrolled_at: datetime
    completion_date: Optional[datetime] = None


class CourseLaunchResponse(BaseModel):
    provider: str
    is_demo: bool
    course_id: uuid.UUID
    external_course_id: str
    course_title: str
    launch_url: str


class LearningEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    external_course_id: str
    course_title: str
    status: str
    progress_percentage: float
    enrolled_at: datetime
    message: str


class LearningHistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enrollment_id: uuid.UUID
    course_id: uuid.UUID
    external_course_id: str
    title: str
    provider: str
    provider_name: str
    difficulty: str
    duration_minutes: int
    progress_percentage: float
    status: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    is_demo: bool = True


class ProviderInfoResponse(BaseModel):
    code: str
    name: str
    provider_type: str  # "DEMO" or "LIVE"
    description: str
    is_active: bool
    is_configured: bool

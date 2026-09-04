import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class OptionResponse(BaseModel):
    id: uuid.UUID
    text: str

    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: uuid.UUID
    text: str
    question_type: str
    options: List[OptionResponse]

    class Config:
        from_attributes = True

class AssessmentResponse(BaseModel):
    id: uuid.UUID
    course_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    pass_percentage: float
    is_ai_generated: bool

    class Config:
        from_attributes = True

class AssessmentStartResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment_id: uuid.UUID
    started_at: datetime
    questions: List[QuestionResponse]

class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID

class AssessmentSubmitRequest(BaseModel):
    answers: List[AnswerSubmit]

class AssessmentAttemptResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    user_id: uuid.UUID
    score: float
    is_passed: bool
    duration_seconds: int
    started_at: datetime
    completed_at: datetime

    class Config:
        from_attributes = True

class CompetencyPerformance(BaseModel):
    competency_code: str
    competency_name: str
    score: float
    questions_answered: int
    questions_correct: int

class AssessmentResultResponse(BaseModel):
    attempt: AssessmentAttemptResponse
    score: float
    is_passed: bool
    competency_performances: List[CompetencyPerformance]


# ==========================================
# PHASE 5 AI MCQ GENERATION SCHEMAS
# ==========================================
class GeneratedMCQOption(BaseModel):
    text: str

class GeneratedMCQ(BaseModel):
    question: str
    options: List[GeneratedMCQOption]
    correct_answer: int  # index of correct option (0-3)
    explanation: str
    competency_code: str
    difficulty: str
    confidence: float = 0.9
    source_page: Optional[int] = None
    grounding_score: Optional[float] = None
    source_chunk_ids: List[uuid.UUID] = []

class GenerationRequest(BaseModel):
    competency_id: uuid.UUID
    difficulty: str = "MEDIUM"
    count: int = 5

class GenerationResponse(BaseModel):
    document_id: uuid.UUID
    competency: str
    generated: int
    accepted: int
    rejected: int
    questions: List[GeneratedMCQ]


import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content")

class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or question")
    user_id: Optional[uuid.UUID] = Field(None, description="Optional user ID for personalized skill gap & recommendation context")
    context_type: Optional[str] = Field(None, description="Optional context type (e.g. 'skill_gap', 'recommendation', 'general')")
    resource_id: Optional[uuid.UUID] = Field(None, description="Optional course/resource ID to explain")
    document_id: Optional[uuid.UUID] = Field(None, description="Optional target document ID to filter RAG context")
    competency_id: Optional[uuid.UUID] = Field(None, description="Optional competency ID to focus topic")
    session_id: Optional[str] = Field(default="default_session", description="Session identifier for multi-turn conversations")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Recent conversation turns")

class CopilotCitation(BaseModel):
    document_id: uuid.UUID
    document_title: str
    document_filename: str
    page: Optional[int] = None
    slide: Optional[int] = None
    source_type: str = "page"
    text_snippet: str
    similarity: float

class CopilotChatResponse(BaseModel):
    reply: str
    citations: List[CopilotCitation] = Field(default_factory=list)
    model: str
    grounded: bool
    session_id: str

class QuickPrompt(BaseModel):
    title: str
    prompt: str
    category: str
    icon: Optional[str] = None

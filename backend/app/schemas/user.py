import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class RoleSimpleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileSimpleResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    job_role_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    organization_id: Optional[uuid.UUID] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    organization_id: Optional[uuid.UUID] = None
    roles: List[RoleSimpleResponse] = []
    profile: Optional[ProfileSimpleResponse] = None
    created_at: datetime
    has_completed_assessment: bool = False

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = "access"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class RoleCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    department: Optional[str] = None

class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RoleCompetencyDetail(BaseModel):
    code: str
    name: str
    required_level: int
    weight: float
    mandatory: bool

class RoleCompetencyResponse(BaseModel):
    role: str
    competencies: List[RoleCompetencyDetail]

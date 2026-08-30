import uuid
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional

class ProfileCreate(BaseModel):
    first_name: str
    last_name: str
    designation: str
    department: str
    contact_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_joining: Optional[date] = None
    bio: Optional[str] = None

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    contact_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_joining: Optional[date] = None
    bio: Optional[str] = None

class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    designation: str
    department: str
    contact_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_joining: Optional[date] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

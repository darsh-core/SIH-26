from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://darshini@localhost:5433/skillstat")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String)
    experience_years = Column(Integer)
    role_id = Column(Integer, ForeignKey("roles.id"))
    
    role = relationship("Role")
    user_skills = relationship("UserSkill", back_populates="user")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    required_skills = relationship("RoleSkill", back_populates="role")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)

class RoleSkill(Base):
    __tablename__ = "role_skills"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    required_level = Column(Integer) # 1 to 5
    importance = Column(Float) # 0.0 to 1.0
    
    role = relationship("Role", back_populates="required_skills")
    skill = relationship("Skill")

class UserSkill(Base):
    __tablename__ = "user_skills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    current_level = Column(Integer, default=1) # 1 to 5
    assessment_score = Column(Float, nullable=True) # 0.0 to 100.0
    
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill")

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    status = Column(String, default="pending") # pending, completed
    generation_mode = Column(String, default="ollama") # ollama, fallback
    created_at = Column(Integer) # simple timestamp
    completed_at = Column(Integer, nullable=True)
    
    questions = relationship("AssessmentQuestion", back_populates="session")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"))
    skill = Column(String)
    difficulty = Column(String)
    question = Column(String)
    options = Column(String) # JSON string
    correct_answer = Column(Integer)
    explanation = Column(String)
    
    session = relationship("AssessmentSession", back_populates="questions")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    provider = Column(String)
    description = Column(String)
    url = Column(String)
    target_skill_id = Column(Integer, ForeignKey("skills.id"))
    difficulty_level = Column(Integer) # 1 to 5
    
    target_skill = relationship("Skill")

# Create tables
Base.metadata.create_all(bind=engine)

import enum

class DocumentState(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    READY_FOR_EMBEDDING = "READY_FOR_EMBEDDING"
    EMBEDDING = "EMBEDDING"
    EMBEDDED = "EMBEDDED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_filename = Column(String)
    safe_filename = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    upload_timestamp = Column(Integer)
    processing_status = Column(String, default=DocumentState.UPLOADED.value)
    processing_error = Column(String, nullable=True)
    extracted_text = Column(String, nullable=True) # JSON normalized representation
    document_hash = Column(String) # SHA-256
    created_at = Column(Integer)
    updated_at = Column(Integer)

    user = relationship("User", back_populates="documents")

User.documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(String)
    estimated_token_count = Column(Integer)
    character_count = Column(Integer)
    source_metadata = Column(String) # JSON containing page, slide, heading, original_filename
    chunk_hash = Column(String)
    created_at = Column(Integer)

    document = relationship("Document", back_populates="chunks")

Document.chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

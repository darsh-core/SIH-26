import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class CompetencyFramework(Base):
    __tablename__ = "competency_framework"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    competencies: Mapped[list["Competency"]] = relationship("Competency", back_populates="framework", cascade="all, delete-orphan")


class Competency(Base):
    __tablename__ = "competency"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency_framework.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    framework: Mapped[CompetencyFramework] = relationship("CompetencyFramework", back_populates="competencies")
    levels: Mapped[list["CompetencyLevel"]] = relationship("CompetencyLevel", back_populates="competency", cascade="all, delete-orphan")
    role_competencies: Mapped[list["RoleCompetency"]] = relationship("RoleCompetency", back_populates="competency", cascade="all, delete-orphan")
    user_competencies: Mapped[list["UserCompetency"]] = relationship("UserCompetency", back_populates="competency", cascade="all, delete-orphan")
    course_competencies: Mapped[list["CourseCompetency"]] = relationship("CourseCompetency", back_populates="competency", cascade="all, delete-orphan")
    training_competencies: Mapped[list["TrainingCompetency"]] = relationship("TrainingCompetency", back_populates="competency", cascade="all, delete-orphan")
    question_competencies: Mapped[list["QuestionCompetency"]] = relationship("QuestionCompetency", back_populates="competency", cascade="all, delete-orphan")


class CompetencyLevel(Base):
    __tablename__ = "competency_level"
    __table_args__ = (
        UniqueConstraint("competency_id", "level", name="uq_competency_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    behavior_indicators: Mapped[list] = mapped_column(JSONB, nullable=True, default=list) # List of descriptive points
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    competency: Mapped[Competency] = relationship("Competency", back_populates="levels")


class JobRole(Base):
    __tablename__ = "job_role"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    department: Mapped[str] = mapped_column(String(150), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    role_competencies: Mapped[list["RoleCompetency"]] = relationship("RoleCompetency", back_populates="job_role", cascade="all, delete-orphan")


class RoleCompetency(Base):
    __tablename__ = "role_competency"
    __table_args__ = (
        UniqueConstraint("job_role_id", "competency_id", name="uq_role_competency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_role.id", ondelete="CASCADE"), nullable=False)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job_role: Mapped[JobRole] = relationship("JobRole", back_populates="role_competencies")
    competency: Mapped[Competency] = relationship("Competency", back_populates="role_competencies")


class UserCompetency(Base):
    __tablename__ = "user_competency"
    __table_args__ = (
        UniqueConstraint("user_id", "competency_id", name="uq_user_competency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    current_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_level: Mapped[int] = mapped_column(Integer, nullable=True)
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="EVALUATED", nullable=False) # EVALUATED, ACQUIRING, GAP
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="user_competencies")
    competency: Mapped[Competency] = relationship("Competency", back_populates="user_competencies")
    evidences: Mapped[list["CompetencyEvidence"]] = relationship("CompetencyEvidence", back_populates="user_competency", cascade="all, delete-orphan")


class CompetencyEvidence(Base):
    __tablename__ = "competency_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_competency.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False) # ASSESSMENT, COURSE_COMPLETION, CERTIFICATE, WORK_EVIDENCE
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True) # ID of assessment_attempt, learning_progress_item, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    verified_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True) # User ID of supervisor
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user_competency: Mapped[UserCompetency] = relationship("UserCompetency", back_populates="evidences")

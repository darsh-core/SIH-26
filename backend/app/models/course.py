import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Date, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Provider(Base):
    __tablename__ = "provider"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False) # ACTIVE, INACTIVE
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="provider", cascade="all, delete-orphan")
    training_programs: Mapped[list["TrainingProgram"]] = relationship("TrainingProgram", back_populates="provider", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "course"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("provider.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False) # Beginner, Intermediate, Advanced
    language: Mapped[str] = mapped_column(String(100), nullable=False, default="English")
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    provider: Mapped[Provider] = relationship("Provider", back_populates="courses")
    course_competencies: Mapped[list["CourseCompetency"]] = relationship("CourseCompetency", back_populates="course", cascade="all, delete-orphan")
    learning_progresses: Mapped[list["LearningProgress"]] = relationship("LearningProgress", back_populates="course", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")


class CourseCompetency(Base):
    __tablename__ = "course_competency"
    __table_args__ = (
        UniqueConstraint("course_id", "competency_id", name="uq_course_competency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    course: Mapped[Course] = relationship("Course", back_populates="course_competencies")
    competency: Mapped["Competency"] = relationship("Competency", back_populates="course_competencies")


class TrainingProgram(Base):
    __tablename__ = "training_program"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("provider.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location: Mapped[str] = mapped_column(String(255), nullable=True) # Location or "Online"
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="OFFLINE") # OFFLINE, ONLINE, HYBRID
    eligibility_criteria: Mapped[str] = mapped_column(Text, nullable=True)
    tpac_recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    provider: Mapped[Provider] = relationship("Provider", back_populates="training_programs")
    training_competencies: Mapped[list["TrainingCompetency"]] = relationship("TrainingCompetency", back_populates="training_program", cascade="all, delete-orphan")
    learning_progresses: Mapped[list["LearningProgress"]] = relationship("LearningProgress", back_populates="training_program", cascade="all, delete-orphan")


class TrainingCompetency(Base):
    __tablename__ = "training_competency"
    __table_args__ = (
        UniqueConstraint("training_program_id", "competency_id", name="uq_training_competency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_program.id", ondelete="CASCADE"), nullable=False)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    target_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    training_program: Mapped[TrainingProgram] = relationship("TrainingProgram", back_populates="training_competencies")
    competency: Mapped["Competency"] = relationship("Competency", back_populates="training_competencies")


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False) # COURSE, TRAINING_PROGRAM
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="SET NULL"), nullable=True)
    training_program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_program.id", ondelete="SET NULL"), nullable=True)
    enrollment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completion_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="ENROLLED", nullable=False) # ENROLLED, IN_PROGRESS, COMPLETED, DROPPED
    certificate_url: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="learning_progresses")
    course: Mapped[Course] = relationship("Course", back_populates="learning_progresses")
    training_program: Mapped[TrainingProgram] = relationship("TrainingProgram", back_populates="learning_progresses")

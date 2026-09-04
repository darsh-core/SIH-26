import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Date, UniqueConstraint, func, Boolean
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
    modules: Mapped[list["CourseModule"]] = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.sequence_order")


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
    module_progresses: Mapped[list["LearningModuleProgress"]] = relationship("LearningModuleProgress", back_populates="learning_progress", cascade="all, delete-orphan")


class CourseModule(Base):
    __tablename__ = "course_module"
    __table_args__ = (
        UniqueConstraint("course_id", "code", name="uq_course_module_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    lessons: Mapped[list["CourseLesson"]] = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan", order_by="CourseLesson.sequence_order")
    module_progresses: Mapped[list["LearningModuleProgress"]] = relationship("LearningModuleProgress", back_populates="module", cascade="all, delete-orphan")


class CourseLesson(Base):
    __tablename__ = "course_lesson"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_module.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    module: Mapped["CourseModule"] = relationship("CourseModule", back_populates="lessons")


class LearningModuleProgress(Base):
    __tablename__ = "learning_module_progress"
    __table_args__ = (
        UniqueConstraint("learning_progress_id", "module_id", name="uq_learning_module_progress"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_progress_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_progress.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course_module.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED", nullable=False) # NOT_STARTED, IN_PROGRESS, COMPLETED
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    learning_progress: Mapped["LearningProgress"] = relationship("LearningProgress", back_populates="module_progresses")
    module: Mapped["CourseModule"] = relationship("CourseModule", back_populates="module_progresses")

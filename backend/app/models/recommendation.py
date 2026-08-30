import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Date, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False) # COURSE, TRAINING_PROGRAM
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="SET NULL"), nullable=True)
    training_program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_program.id", ondelete="SET NULL"), nullable=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False)
    
    gap_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0) # Gap size (e.g. required_level - current_level)
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0) # Calculated sorting score
    logic_explanation: Mapped[str] = mapped_column(Text, nullable=True) # Reason why it was recommended
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0) # Confidence level of recommendation
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, ACCEPTED, REJECTED, COMPLETED
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="recommendations")
    course: Mapped["Course"] = relationship("Course")
    training_program: Mapped["TrainingProgram"] = relationship("TrainingProgram")
    competency: Mapped["Competency"] = relationship("Competency")
    plan_items: Mapped[list["LearningPlanItem"]] = relationship("LearningPlanItem", back_populates="recommendation")


class LearningPlan(Base):
    __tablename__ = "learning_plan"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False) # ACTIVE, COMPLETED, ARCHIVED
    target_completion_date: Mapped[Date] = mapped_column(Date, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="learning_plans")
    items: Mapped[list["LearningPlanItem"]] = relationship("LearningPlanItem", back_populates="learning_plan", cascade="all, delete-orphan")


class LearningPlanItem(Base):
    __tablename__ = "learning_plan_item"
    __table_args__ = (
        # Prevent duplicate courses or training programs in the same learning plan
        UniqueConstraint("learning_plan_id", "course_id", name="uq_plan_course"),
        UniqueConstraint("learning_plan_id", "training_program_id", name="uq_plan_training"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_plan.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False) # COURSE, TRAINING_PROGRAM
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=True)
    training_program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_program.id", ondelete="CASCADE"), nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False) # PENDING, IN_PROGRESS, COMPLETED, SKIPPED
    added_from_recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    learning_plan: Mapped[LearningPlan] = relationship("LearningPlan", back_populates="items")
    course: Mapped["Course"] = relationship("Course")
    training_program: Mapped["TrainingProgram"] = relationship("TrainingProgram")
    recommendation: Mapped[Recommendation] = relationship("Recommendation", back_populates="plan_items")

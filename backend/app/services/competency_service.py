import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status

from app.models.competency import (
    CompetencyFramework,
    Competency,
    CompetencyLevel,
    JobRole,
    RoleCompetency,
    UserCompetency,
    CompetencyEvidence,
)
from app.models.course import Course, CourseCompetency
from app.schemas.competency import CompetencyUpdateRequest

class CompetencyService:
    
    @staticmethod
    def get_competencies(
        db: Session,
        framework_name: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Competency], int]:
        query = db.query(Competency)
        
        if framework_name:
            query = query.join(CompetencyFramework).filter(
                func.lower(CompetencyFramework.name) == framework_name.lower()
            )
            
        if search:
            query = query.filter(
                or_(
                    Competency.name.ilike(f"%{search}%"),
                    Competency.code.ilike(f"%{search}%"),
                    Competency.description.ilike(f"%{search}%")
                )
            )
            
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_competency(db: Session, competency_id: uuid.UUID) -> Optional[Competency]:
        return db.query(Competency).filter(Competency.id == competency_id).first()

    @staticmethod
    def get_competency_by_code(db: Session, code: str) -> Optional[Competency]:
        return db.query(Competency).filter(Competency.code == code).first()

    @staticmethod
    def get_competency_levels(db: Session, competency_id: uuid.UUID) -> List[CompetencyLevel]:
        return db.query(CompetencyLevel).filter(CompetencyLevel.competency_id == competency_id).order_by(CompetencyLevel.level).all()

    @staticmethod
    def get_competency_roles(db: Session, competency_id: uuid.UUID) -> List[JobRole]:
        return db.query(JobRole).join(RoleCompetency).filter(RoleCompetency.competency_id == competency_id).all()

    @staticmethod
    def get_competency_courses(db: Session, competency_id: uuid.UUID) -> List[Course]:
        return db.query(Course).join(CourseCompetency).filter(CourseCompetency.competency_id == competency_id).all()

    @staticmethod
    def get_user_competencies(db: Session, user_id: uuid.UUID) -> List[UserCompetency]:
        return db.query(UserCompetency).filter(UserCompetency.user_id == user_id).all()

    @staticmethod
    def get_user_evidence(db: Session, user_id: uuid.UUID) -> List[CompetencyEvidence]:
        return db.query(CompetencyEvidence).join(UserCompetency).filter(UserCompetency.user_id == user_id).order_by(CompetencyEvidence.created_at.desc()).all()

    @staticmethod
    def update_user_competency(
        db: Session,
        user_id: uuid.UUID,
        competency_id: uuid.UUID,
        update_in: CompetencyUpdateRequest,
        source_id: Optional[uuid.UUID] = None,
        verified_by: Optional[uuid.UUID] = None,
    ) -> UserCompetency:
        # Verify competency exists
        competency = CompetencyService.get_competency(db, competency_id)
        if not competency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competency with ID {competency_id} not found"
            )
            
        # Find or create user competency
        user_comp = db.query(UserCompetency).filter(
            UserCompetency.user_id == user_id,
            UserCompetency.competency_id == competency_id
        ).first()
        
        old_level = 0.0
        if not user_comp:
            user_comp = UserCompetency(
                user_id=user_id,
                competency_id=competency_id,
                current_level=update_in.current_level,
                last_evaluated_at=datetime.utcnow(),
                status="EVALUATED"
            )
            db.add(user_comp)
            db.flush()
        else:
            old_level = user_comp.current_level
            user_comp.current_level = update_in.current_level
            user_comp.last_evaluated_at = datetime.utcnow()
            user_comp.status = "EVALUATED"
            
        # Write to evidence table to track audit changes
        evidence = CompetencyEvidence(
            user_competency_id=user_comp.id,
            type=update_in.source,
            source_id=source_id,
            description=f"Competency updated from {old_level:.1f} to {update_in.current_level:.1f} via {update_in.source.lower()}.",
            verified_by=verified_by,
            verified_at=datetime.utcnow() if verified_by else None,
            metadata_json={"old_level": old_level, "new_level": update_in.current_level, "confidence": update_in.confidence}
        )
        db.add(evidence)
        db.commit()
        db.refresh(user_comp)
        return user_comp

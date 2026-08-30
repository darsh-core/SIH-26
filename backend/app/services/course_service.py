import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.course import Course, Provider, TrainingProgram

class CourseService:
    
    @staticmethod
    def get_providers(db: Session, skip: int = 0, limit: int = 10) -> Tuple[List[Provider], int]:
        query = db.query(Provider)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_courses(db: Session, skip: int = 0, limit: int = 10) -> Tuple[List[Course], int]:
        query = db.query(Course)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_training_programs(db: Session, skip: int = 0, limit: int = 10) -> Tuple[List[TrainingProgram], int]:
        query = db.query(TrainingProgram)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

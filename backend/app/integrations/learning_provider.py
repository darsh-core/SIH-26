import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.course import (
    Provider,
    Course,
    CourseCompetency,
    CourseModule,
    CourseLesson,
    LearningProgress,
    LearningModuleProgress,
)
from app.models.competency import Competency
from app.schemas.learning import (
    NormalizedLearningResource,
    LearningCompetencyDetail,
    LearningModuleDetail,
    LearningLessonDetail,
    LearningEnrollmentResponse,
    CourseLaunchResponse,
    LearningProgressDetailResponse,
    ModuleProgressStatus,
    LearningHistoryItemResponse,
)


class LearningProvider(ABC):
    """
    Abstract Base Class defining the SANKHYAI Learning Provider contract.
    Both DemoIGOTProvider and future real IGOTProvider implement this exact interface.
    """

    @abstractmethod
    def search_courses(
        self,
        db: Session,
        competency_codes: Optional[List[str]] = None,
        role_id: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[NormalizedLearningResource]:
        """Search and filter courses based on competencies, role, and difficulty."""
        pass

    @abstractmethod
    def get_course(
        self, db: Session, course_id_or_code: str
    ) -> Optional[NormalizedLearningResource]:
        """Retrieve a specific course by its internal UUID or external code."""
        pass

    @abstractmethod
    def enroll(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningEnrollmentResponse:
        """Idempotently enroll an employee into a course."""
        pass

    @abstractmethod
    def launch_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> CourseLaunchResponse:
        """Launch the course player and return the authorized launch route."""
        pass

    @abstractmethod
    def get_progress(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        """Retrieve detailed module-by-module learning progress."""
        pass

    @abstractmethod
    def complete_module(
        self,
        db: Session,
        user_id: uuid.UUID,
        course_id_or_code: str,
        module_id_or_code: str,
    ) -> LearningProgressDetailResponse:
        """Mark a module as completed and recalculate progress percentage."""
        pass

    @abstractmethod
    def complete_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        """Mark the entire course as completed and log to learning history."""
        pass

    @abstractmethod
    def get_learning_history(
        self, db: Session, user_id: uuid.UUID
    ) -> List[LearningHistoryItemResponse]:
        """Retrieve the employee's historical course enrollments and completions."""
        pass


class DemoIGOTProvider(LearningProvider):
    """
    Concrete SANKHYAI Demo iGOT Provider.
    Implements the real learning workflow backed by SANKHYAI's PostgreSQL database
    seeded with official MoSPI competency courses, modules, and lessons.
    """

    def _resolve_course(self, db: Session, course_id_or_code: str) -> Course:
        """Helper to find a course by UUID or code."""
        try:
            course_uuid = uuid.UUID(str(course_id_or_code))
            course = (
                db.query(Course)
                .options(
                    joinedload(Course.provider),
                    joinedload(Course.course_competencies).joinedload(CourseCompetency.competency),
                    joinedload(Course.modules).joinedload(CourseModule.lessons),
                )
                .filter(Course.id == course_uuid)
                .first()
            )
        except ValueError:
            course = (
                db.query(Course)
                .options(
                    joinedload(Course.provider),
                    joinedload(Course.course_competencies).joinedload(CourseCompetency.competency),
                    joinedload(Course.modules).joinedload(CourseModule.lessons),
                )
                .filter(Course.code == course_id_or_code)
                .first()
            )

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning resource '{course_id_or_code}' not found.",
            )
        return course

    def _to_normalized(self, course: Course) -> NormalizedLearningResource:
        """Convert a SQLAlchemy Course model to NormalizedLearningResource."""
        comp_details = []
        for cc in course.course_competencies:
            if cc.competency:
                comp_details.append(
                    LearningCompetencyDetail(
                        code=cc.competency.code,
                        name=cc.competency.name,
                        target_level=cc.target_level,
                        weight=cc.weight,
                    )
                )

        modules_details = []
        sorted_modules = sorted(course.modules, key=lambda m: m.sequence_order)
        for m in sorted_modules:
            sorted_lessons = sorted(m.lessons, key=lambda l: l.sequence_order)
            lessons_details = [
                LearningLessonDetail(
                    id=l.id,
                    title=l.title,
                    content=l.content,
                    duration_minutes=l.duration_minutes,
                    sequence_order=l.sequence_order,
                )
                for l in sorted_lessons
            ]
            modules_details.append(
                LearningModuleDetail(
                    id=m.id,
                    code=m.code,
                    title=m.title,
                    description=m.description,
                    duration_minutes=m.duration_minutes,
                    sequence_order=m.sequence_order,
                    is_required=m.is_required,
                    lessons=lessons_details,
                )
            )

        provider_name = course.provider.name if course.provider else "iGOT Karmayogi"

        return NormalizedLearningResource(
            id=course.id,
            provider="igot",
            provider_name=provider_name,
            external_course_id=course.code,
            title=course.title,
            description=course.description,
            duration_minutes=course.duration_minutes,
            difficulty=course.difficulty,
            language=course.language,
            course_url=course.url or f"/demo-igot/courses/{course.id}",
            is_demo=True,
            competencies=comp_details,
            modules=modules_details,
            metadata_json=course.metadata_json or {},
        )

    def search_courses(
        self,
        db: Session,
        competency_codes: Optional[List[str]] = None,
        role_id: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[NormalizedLearningResource]:
        query = db.query(Course).options(
            joinedload(Course.provider),
            joinedload(Course.course_competencies).joinedload(CourseCompetency.competency),
            joinedload(Course.modules).joinedload(CourseModule.lessons),
        )

        if difficulty:
            query = query.filter(Course.difficulty.ilike(difficulty))

        courses = query.offset(skip).limit(limit).all()

        results = []
        for c in courses:
            # If competency filter provided, check matching
            if competency_codes:
                matched = any(
                    cc.competency and cc.competency.code in competency_codes
                    for cc in c.course_competencies
                )
                if not matched:
                    continue
            results.append(self._to_normalized(c))

        return results

    def get_course(
        self, db: Session, course_id_or_code: str
    ) -> Optional[NormalizedLearningResource]:
        course = self._resolve_course(db, course_id_or_code)
        return self._to_normalized(course)

    def enroll(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningEnrollmentResponse:
        course = self._resolve_course(db, course_id_or_code)

        # Idempotency check: return existing enrollment if user is already enrolled
        existing = (
            db.query(LearningProgress)
            .filter(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == course.id,
            )
            .first()
        )

        if existing:
            return LearningEnrollmentResponse(
                enrollment_id=existing.id,
                user_id=user_id,
                course_id=course.id,
                external_course_id=course.code,
                course_title=course.title,
                status=existing.status,
                progress_percentage=existing.progress_percentage,
                enrolled_at=existing.enrollment_date,
                message="Already enrolled in this course.",
            )

        # Create new enrollment
        now = datetime.utcnow()
        new_progress = LearningProgress(
            user_id=user_id,
            item_type="COURSE",
            course_id=course.id,
            enrollment_date=now,
            progress_percentage=0.0,
            status="ENROLLED",
            metadata_json={"provider": "igot", "is_demo": True},
        )
        db.add(new_progress)
        db.flush()

        # Initialize module progress for all modules
        for m in course.modules:
            mod_prog = LearningModuleProgress(
                learning_progress_id=new_progress.id,
                module_id=m.id,
                status="NOT_STARTED",
            )
            db.add(mod_prog)

        db.commit()
        db.refresh(new_progress)

        return LearningEnrollmentResponse(
            enrollment_id=new_progress.id,
            user_id=user_id,
            course_id=course.id,
            external_course_id=course.code,
            course_title=course.title,
            status=new_progress.status,
            progress_percentage=0.0,
            enrolled_at=new_progress.enrollment_date,
            message="Successfully enrolled in course.",
        )

    def launch_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> CourseLaunchResponse:
        course = self._resolve_course(db, course_id_or_code)

        # Auto-enroll if not already enrolled
        self.enroll(db, user_id, course_id_or_code)

        # In Demo mode, launch URL maps to SANKHYAI's internal demo player
        launch_url = f"/demo-igot/courses/{course.id}"

        return CourseLaunchResponse(
            provider="igot",
            is_demo=True,
            course_id=course.id,
            external_course_id=course.code,
            course_title=course.title,
            launch_url=launch_url,
        )

    def get_progress(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        course = self._resolve_course(db, course_id_or_code)

        progress = (
            db.query(LearningProgress)
            .options(
                joinedload(LearningProgress.module_progresses).joinedload(LearningModuleProgress.module)
            )
            .filter(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == course.id,
            )
            .first()
        )

        if not progress:
            # Auto-enroll if requested
            self.enroll(db, user_id, course_id_or_code)
            return self.get_progress(db, user_id, course_id_or_code)

        # Ensure all course modules have a progress entry
        existing_module_ids = {mp.module_id for mp in progress.module_progresses}
        needs_commit = False
        for m in course.modules:
            if m.id not in existing_module_ids:
                new_mp = LearningModuleProgress(
                    learning_progress_id=progress.id,
                    module_id=m.id,
                    status="NOT_STARTED",
                )
                db.add(new_mp)
                needs_commit = True

        if needs_commit:
            db.commit()
            db.refresh(progress)

        # Build module status list sorted by module sequence_order
        mod_statuses = []
        completed_count = 0
        sorted_modules = sorted(course.modules, key=lambda m: m.sequence_order)

        mp_dict = {mp.module_id: mp for mp in progress.module_progresses}
        for m in sorted_modules:
            mp = mp_dict.get(m.id)
            st = mp.status if mp else "NOT_STARTED"
            cat = mp.completed_at if mp else None
            if st == "COMPLETED":
                completed_count += 1
            mod_statuses.append(
                ModuleProgressStatus(
                    module_id=m.id,
                    module_code=m.code,
                    module_title=m.title,
                    sequence_order=m.sequence_order,
                    status=st,
                    completed_at=cat,
                )
            )

        total_modules = len(sorted_modules)

        return LearningProgressDetailResponse(
            enrollment_id=progress.id,
            user_id=user_id,
            course_id=course.id,
            external_course_id=course.code,
            course_title=course.title,
            provider_name=course.provider.name if course.provider else "iGOT Karmayogi",
            is_demo=True,
            progress_percentage=progress.progress_percentage,
            status=progress.status,
            completed_modules=completed_count,
            total_modules=total_modules,
            modules=mod_statuses,
            enrolled_at=progress.enrollment_date,
            completion_date=progress.completion_date,
        )

    def complete_module(
        self,
        db: Session,
        user_id: uuid.UUID,
        course_id_or_code: str,
        module_id_or_code: str,
    ) -> LearningProgressDetailResponse:
        course = self._resolve_course(db, course_id_or_code)

        progress = (
            db.query(LearningProgress)
            .filter(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == course.id,
            )
            .first()
        )

        if not progress:
            self.enroll(db, user_id, course_id_or_code)
            progress = (
                db.query(LearningProgress)
                .filter(
                    LearningProgress.user_id == user_id,
                    LearningProgress.course_id == course.id,
                )
                .first()
            )

        # Resolve target module
        target_mod = None
        for m in course.modules:
            if str(m.id) == str(module_id_or_code) or m.code == module_id_or_code:
                target_mod = m
                break

        if not target_mod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module '{module_id_or_code}' not found in course.",
            )

        # Find or create module progress
        mod_prog = (
            db.query(LearningModuleProgress)
            .filter(
                LearningModuleProgress.learning_progress_id == progress.id,
                LearningModuleProgress.module_id == target_mod.id,
            )
            .first()
        )

        now = datetime.utcnow()
        if not mod_prog:
            mod_prog = LearningModuleProgress(
                learning_progress_id=progress.id,
                module_id=target_mod.id,
                status="COMPLETED",
                completed_at=now,
            )
            db.add(mod_prog)
        else:
            mod_prog.status = "COMPLETED"
            if not mod_prog.completed_at:
                mod_prog.completed_at = now

        db.flush()

        # Recalculate course overall progress percentage
        all_mod_progs = (
            db.query(LearningModuleProgress)
            .filter(LearningModuleProgress.learning_progress_id == progress.id)
            .all()
        )
        completed_count = sum(1 for mp in all_mod_progs if mp.status == "COMPLETED")
        total_count = len(course.modules) if course.modules else 1
        new_percentage = round((completed_count / total_count) * 100.0, 1)

        progress.progress_percentage = min(100.0, new_percentage)
        if progress.progress_percentage >= 100.0:
            progress.status = "COMPLETED"
            if not progress.completion_date:
                progress.completion_date = now
        else:
            progress.status = "IN_PROGRESS"

        db.commit()

        return self.get_progress(db, user_id, str(course.id))

    def complete_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        course = self._resolve_course(db, course_id_or_code)

        progress = (
            db.query(LearningProgress)
            .filter(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id == course.id,
            )
            .first()
        )

        if not progress:
            self.enroll(db, user_id, course_id_or_code)
            progress = (
                db.query(LearningProgress)
                .filter(
                    LearningProgress.user_id == user_id,
                    LearningProgress.course_id == course.id,
                )
                .first()
            )

        now = datetime.utcnow()
        # Mark all modules as completed
        for m in course.modules:
            mod_prog = (
                db.query(LearningModuleProgress)
                .filter(
                    LearningModuleProgress.learning_progress_id == progress.id,
                    LearningModuleProgress.module_id == m.id,
                )
                .first()
            )
            if not mod_prog:
                mod_prog = LearningModuleProgress(
                    learning_progress_id=progress.id,
                    module_id=m.id,
                    status="COMPLETED",
                    completed_at=now,
                )
                db.add(mod_prog)
            else:
                mod_prog.status = "COMPLETED"
                if not mod_prog.completed_at:
                    mod_prog.completed_at = now

        progress.progress_percentage = 100.0
        progress.status = "COMPLETED"
        progress.completion_date = now
        db.commit()

        return self.get_progress(db, user_id, str(course.id))

    def get_learning_history(
        self, db: Session, user_id: uuid.UUID
    ) -> List[LearningHistoryItemResponse]:
        progresses = (
            db.query(LearningProgress)
            .options(
                joinedload(LearningProgress.course).joinedload(Course.provider)
            )
            .filter(
                LearningProgress.user_id == user_id,
                LearningProgress.course_id.isnot(None),
            )
            .order_by(LearningProgress.enrollment_date.desc())
            .all()
        )

        items = []
        for p in progresses:
            if not p.course:
                continue
            provider_name = p.course.provider.name if p.course.provider else "iGOT Karmayogi"
            items.append(
                LearningHistoryItemResponse(
                    enrollment_id=p.id,
                    course_id=p.course.id,
                    external_course_id=p.course.code,
                    title=p.course.title,
                    provider="igot",
                    provider_name=provider_name,
                    difficulty=p.course.difficulty,
                    duration_minutes=p.course.duration_minutes,
                    progress_percentage=p.progress_percentage,
                    status=p.status,
                    enrolled_at=p.enrollment_date,
                    completed_at=p.completion_date,
                    is_demo=True,
                )
            )
        return items


class IGOTProvider(LearningProvider):
    """
    Official iGOT Karmayogi Provider Interface for future production integration.
    Ready to receive official OAuth2/SSO credentials and base API endpoints.
    """

    def __init__(self):
        self.api_base_url = settings.IGOT_API_BASE_URL
        self.client_id = settings.IGOT_CLIENT_ID
        self.client_secret = settings.IGOT_CLIENT_SECRET
        self.is_configured = bool(self.api_base_url and self.client_id and self.client_secret)

    def _ensure_configured(self):
        if not self.is_configured:
            raise NotImplementedError(
                "Official iGOT Karmayogi API credentials not configured. "
                "Please obtain OAuth2 credentials from the iGOT Karmayogi team or "
                "set LEARNING_PROVIDER=demo in the environment to use the demo integration."
            )

    def search_courses(
        self,
        db: Session,
        competency_codes: Optional[List[str]] = None,
        role_id: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[NormalizedLearningResource]:
        self._ensure_configured()
        return []

    def get_course(
        self, db: Session, course_id_or_code: str
    ) -> Optional[NormalizedLearningResource]:
        self._ensure_configured()
        return None

    def enroll(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningEnrollmentResponse:
        self._ensure_configured()
        raise NotImplementedError("Live iGOT enrollment requires official credentials.")

    def launch_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> CourseLaunchResponse:
        self._ensure_configured()
        raise NotImplementedError("Live iGOT launch requires official credentials.")

    def get_progress(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        self._ensure_configured()
        raise NotImplementedError("Live iGOT progress tracking requires official credentials.")

    def complete_module(
        self,
        db: Session,
        user_id: uuid.UUID,
        course_id_or_code: str,
        module_id_or_code: str,
    ) -> LearningProgressDetailResponse:
        self._ensure_configured()
        raise NotImplementedError("Live iGOT completion requires official credentials.")

    def complete_course(
        self, db: Session, user_id: uuid.UUID, course_id_or_code: str
    ) -> LearningProgressDetailResponse:
        self._ensure_configured()
        raise NotImplementedError("Live iGOT completion requires official credentials.")

    def get_learning_history(
        self, db: Session, user_id: uuid.UUID
    ) -> List[LearningHistoryItemResponse]:
        self._ensure_configured()
        return []


def get_learning_provider() -> LearningProvider:
    """
    Provider factory selecting the provider implementation based on environment configuration.
    Defaults to DemoIGOTProvider unless LEARNING_PROVIDER=igot is explicitly configured.
    """
    provider_name = settings.LEARNING_PROVIDER.lower().strip()
    if provider_name == "igot":
        return IGOTProvider()
    return DemoIGOTProvider()

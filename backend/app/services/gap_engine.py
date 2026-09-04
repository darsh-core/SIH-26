import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import AppUser, UserProfile
from app.models.competency import JobRole, RoleCompetency, UserCompetency, Competency
from app.schemas.recommendation import UserCompetencyGapsResponse, CompetencyGapDetail, RoleInfo

class GapEngine:
    
    # Configurable weighting multipliers
    MANDATORY_MULTIPLIER = 1.5
    DEFAULT_CONFIDENCE = 1.0
    DEFAULT_ASSIGNMENT_RELEVANCE = 1.0

    @staticmethod
    def calculate_gaps(db: Session, user_id: uuid.UUID) -> UserCompetencyGapsResponse:
        # Get User
        user = db.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        # Get profile and job role
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile or not profile.job_role_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User profile or Job Role association is missing. Please map the user to a job role."
            )

        job_role = db.query(JobRole).filter(JobRole.id == profile.job_role_id).first()
        if not job_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned Job Role not found"
            )

        # Load role competencies
        role_competencies = db.query(RoleCompetency).filter(
            RoleCompetency.job_role_id == job_role.id
        ).all()

        # Load user competencies
        user_comps = db.query(UserCompetency).filter(
            UserCompetency.user_id == user_id
        ).all()
        user_comp_map = {uc.competency_id: uc.current_level for uc in user_comps}

        # Calculate achievement and aggregate variables
        total_weight = 0.0
        weighted_achievement_sum = 0.0
        gaps_list: List[CompetencyGapDetail] = []
        
        high_gaps = 0
        med_gaps = 0
        low_gaps = 0

        for rc in role_competencies:
            competency = rc.competency
            required = float(rc.required_level)
            current = float(user_comp_map.get(rc.competency_id, 0.0))

            # Math formulas
            gap = max(0.0, required - current)
            normalized_gap = gap / required if required > 0.0 else 0.0

            # Priority calculations
            mandatory_mult = GapEngine.MANDATORY_MULTIPLIER if rc.is_mandatory else 1.0
            
            # Priority Score
            priority_score = (
                normalized_gap *
                rc.weight *
                mandatory_mult *
                GapEngine.DEFAULT_CONFIDENCE *
                GapEngine.DEFAULT_ASSIGNMENT_RELEVANCE
            )

            # Categorize priority
            if priority_score >= 0.5:
                priority = "HIGH"
                if gap > 0.0:
                    high_gaps += 1
            elif priority_score >= 0.25:
                priority = "MEDIUM"
                if gap > 0.0:
                    med_gaps += 1
            elif priority_score > 0.0:
                priority = "LOW"
                if gap > 0.0:
                    low_gaps += 1
            else:
                priority = "NONE"

            # Achievement for readiness formula: min(current / required, 1.0)
            achievement = min(current / required, 1.0) if required > 0.0 else 1.0
            
            total_weight += rc.weight
            weighted_achievement_sum += (achievement * rc.weight)

            gaps_list.append(
                CompetencyGapDetail(
                    competency_code=competency.code,
                    competency_name=competency.name,
                    required_level=required,
                    current_level=current,
                    gap=round(gap, 2),
                    normalized_gap=round(normalized_gap, 3),
                    priority=priority,
                    priority_score=round(priority_score, 3),
                    mandatory=rc.is_mandatory,
                    weight=rc.weight
                )
            )

        # Weighted readiness score: sum(achievement * weight) / sum(weight) * 100.0
        overall_readiness = (
            (weighted_achievement_sum / total_weight) * 100.0
            if total_weight > 0.0
            else 100.0
        )

        return UserCompetencyGapsResponse(
            user_id=user_id,
            role=RoleInfo(code=job_role.code, title=job_role.name),
            overall_readiness=round(overall_readiness, 1),
            gaps=gaps_list
        )
        
    @staticmethod
    def get_readiness_metrics(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        gaps_response = GapEngine.calculate_gaps(db, user_id)
        
        # Calculate categories count
        high = 0
        medium = 0
        low = 0
        
        for g in gaps_response.gaps:
            if g.gap > 0.0:
                if g.priority == "HIGH":
                    high += 1
                elif g.priority == "MEDIUM":
                    medium += 1
                elif g.priority == "LOW":
                    low += 1
                    
        return {
            "overall_readiness": gaps_response.overall_readiness,
            "competencies_assessed": len(gaps_response.gaps),
            "high_priority_gaps": high,
            "medium_priority_gaps": medium,
            "low_priority_gaps": low
        }

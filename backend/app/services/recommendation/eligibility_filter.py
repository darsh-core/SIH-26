import uuid
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models.course import Course, TrainingProgram, LearningProgress, Provider
from app.models.user import UserProfile
from app.services.recommendation.candidate_retriever import RecommendationCandidate

class EligibilityFilter:
    
    @staticmethod
    def filter_candidates(
        db: Session,
        user_id: uuid.UUID,
        candidates: List[RecommendationCandidate],
        current_levels: Dict[str, float],
        target_levels: Dict[str, float]
    ) -> List[RecommendationCandidate]:
        """
        Applies hard filters to eliminate completed, inactive, or ineligible candidates.
        """
        # 1. Fetch completed items for the user
        progress_records = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.status == "COMPLETED"
        ).all()
        
        completed_codes = set()
        for pr in progress_records:
            # Map course/training program to its code
            if pr.item_type == "COURSE" and pr.course:
                completed_codes.add(pr.course.code)
            elif pr.item_type == "TRAINING_PROGRAM" and pr.training_program:
                completed_codes.add(pr.training_program.code)
                
        # 2. Fetch user profile for eligibility check
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        user_dept = profile.department.lower() if profile and profile.department else ""
        user_desig = profile.designation.lower() if profile and profile.designation else ""
        
        # 3. Check active providers in DB to filter out inactive resources
        provider_status = {p.name: p.status for p in db.query(Provider).all()}
        provider_name_map = {
            "iGOT": "iGOT Karmayogi",
            "NSSTA": "National Statistical Systems Training Academy (NSSTA)"
        }
        
        filtered = []
        for c in candidates:
            # A. Already Completed check
            if c.code in completed_codes:
                continue
                
            # B. Inactive Provider check
            db_provider_name = provider_name_map.get(c.provider, c.provider)
            if provider_status.get(db_provider_name) != "ACTIVE":
                continue
                
            # C. Eligibility check (Role / Department check if metadata exists)
            if c.eligibility_criteria:
                elig_lower = c.eligibility_criteria.lower()
                
                # If it's a National Accounts specific course and user is not NAD
                if ("national accounts" in elig_lower or "nad" in elig_lower) and "national accounts" not in user_dept:
                    continue
                
                # If it requires Senior / Director roles, and user is regular staff
                if ("senior" in elig_lower or "director" in elig_lower) and not any(k in user_desig for k in ["senior", "director", "supervisor", "manager"]):
                    continue
                    
                # If it specifies Indian Statistical Service (ISS) only and user is SSS / Statistical Officer
                if "iss only" in elig_lower or "iss officers" in elig_lower:
                    if "sss" in user_desig or "statistical officer" in user_desig:
                        # Allow only if it says "ISS or SSS" or similar
                        if "sss" not in elig_lower and "statistical officer" not in elig_lower:
                            continue
                            
            # D. Level hard filter check (excessive level gap)
            # If the course targets a level that is excessively above the target required level + 1.5,
            # it is too advanced for the user's current track.
            # (Example: User current level is 1.0, required is 3.0, course targets level 5.0 -> skip)
            is_excessive = False
            for m in c.competency_mappings:
                user_target = target_levels.get(m.competency_code, 5.0)
                user_current = current_levels.get(m.competency_code, 0.0)
                
                # If course targets more than target_level + 1.5, or targets level 5 when user is still at level 1
                if m.target_level > user_target + 1.5:
                    is_excessive = True
                    break
                # If course targets level 4 or 5 and user is an assessed beginner (0.0 < user_current < 1.5)
                if m.target_level >= 4.0 and 0.0 < user_current < 1.5:
                    is_excessive = True
                    break
                # If course targets a level significantly below the user's current level (more than 1.0 below)
                if m.target_level < user_current - 1.0:
                    is_excessive = True
                    break
                    
            if is_excessive:
                continue
                
            filtered.append(c)
            
        return filtered

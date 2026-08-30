import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.course import Course, TrainingProgram
from app.models.recommendation import Recommendation
from app.services.recommendation.candidate_retriever import RecommendationCandidate

class RankingService:
    
    @staticmethod
    def generate_explanation(
        candidate: RecommendationCandidate,
        comp_name: str,
        current_level: float,
        required_level: float
    ) -> str:
        """
        Generates a human-readable explanation from structured metadata.
        """
        # Determine mapping level
        mapping = next((m for m in candidate.competency_mappings if m.competency_code in comp_name or comp_name in m.competency_code), None)
        target_lvl_str = f"level {mapping.target_level}" if mapping else "the required level"
        
        provider_name = "iGOT Karmayogi" if candidate.provider == "iGOT" else "NSSTA Academy"
        
        reason = (
            f"Recommended because your '{comp_name}' competency is currently {current_level}/5 "
            f"while the target role requires level {required_level}. "
            f"This {provider_name} resource targets {target_lvl_str} and directly addresses this gap."
        )
        
        # Add TPAC endorsement if available
        if candidate.tpac_recommendation:
            reason += f" Specially endorsed: {candidate.tpac_recommendation}"
            
        return reason

    @staticmethod
    def rank_and_persist(
        db: Session,
        user_id: uuid.UUID,
        scored_candidates: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """
        Sorts candidates, saves them to the database, and returns the persisted models.
        """
        # Delete existing pending recommendations for the user to refresh
        db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.status == "PENDING"
        ).delete()
        db.commit()
        
        # Sort by final score descending
        sorted_candidates = sorted(scored_candidates, key=lambda x: x["scores"]["final_score"], reverse=True)
        
        persisted = []
        for item in sorted_candidates:
            candidate = item["candidate"]
            scores = item["scores"]
            comp_id = item["competency_id"]
            comp_code = item["competency_code"]
            gap_size = item["gap_size"]
            reason = item["reason"]
            
            # Map code to course_id / training_program_id
            course_id = None
            training_program_id = None
            
            if candidate.provider == "iGOT":
                db_course = db.query(Course).filter(Course.code == candidate.code).first()
                if db_course:
                    course_id = db_course.id
                item_type = "COURSE"
            else:
                db_prog = db.query(TrainingProgram).filter(TrainingProgram.code == candidate.code).first()
                if db_prog:
                    training_program_id = db_prog.id
                item_type = "TRAINING_PROGRAM"
                
            # If neither found, skip (foreign key safety)
            if not course_id and not training_program_id:
                continue
                
            rec = Recommendation(
                user_id=user_id,
                item_type=item_type,
                course_id=course_id,
                training_program_id=training_program_id,
                competency_id=comp_id,
                gap_score=int(gap_size),
                recommendation_score=scores["final_score"],
                logic_explanation=reason,
                confidence_score=scores["semantic_similarity"],
                status="PENDING"
            )
            db.add(rec)
            persisted.append(rec)
            
        db.commit()
        for r in persisted:
            db.refresh(r)
            
        return persisted

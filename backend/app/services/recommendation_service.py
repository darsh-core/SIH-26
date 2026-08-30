import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.models.competency import Competency
from app.services.gap_engine import GapEngine
from app.services.recommendation import (
    CandidateRetriever,
    EligibilityFilter,
    RecommendationScorer,
    RankingService,
    RecommendationWeights
)

class RecommendationService:
    
    @staticmethod
    def get_recommendations(db: Session, user_id: uuid.UUID) -> List[Recommendation]:
        """
        Fetches existing recommendations. If none exist, generates them.
        """
        recs = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.status == "PENDING"
        ).order_by(Recommendation.recommendation_score.desc()).all()
        
        if not recs:
            recs = RecommendationService.generate_recommendations(db, user_id)
            
        return recs

    @staticmethod
    def generate_recommendations(
        db: Session,
        user_id: uuid.UUID,
        weights: RecommendationWeights = RecommendationWeights()
    ) -> List[Recommendation]:
        """
        Main recommendation engine pipeline orchestration:
        Gaps -> Candidates -> Filter -> Score -> Rank -> Persist.
        """
        # 1. Fetch user competency gaps
        gap_data = GapEngine.calculate_gaps(db, user_id=user_id)
        
        # Build maps for current & target levels and db competency ID lookup
        current_levels = {}
        target_levels = {}
        
        for gap in gap_data.gaps:
            current_levels[gap.competency_code] = gap.current_level
            target_levels[gap.competency_code] = gap.required_level
            
        # Get DB Competency IDs mapped by code
        competencies = db.query(Competency).all()
        comp_id_map = {c.code: c.id for c in competencies}
        
        # Only recommend for competencies with a positive gap
        active_gaps = [g for g in gap_data.gaps if g.gap > 0.0]
        
        scored_candidates = []
        
        for gap in active_gaps:
            comp_id = comp_id_map.get(gap.competency_code)
            if not comp_id:
                continue
                
            # 2. Retrieve candidates addressing this specific competency gap
            candidates = CandidateRetriever.retrieve_candidates([gap.competency_code])
            
            # 3. Filter unsuitable candidates
            filtered = EligibilityFilter.filter_candidates(
                db,
                user_id=user_id,
                candidates=candidates,
                current_levels=current_levels,
                target_levels=target_levels
            )
            
            # 4. Score and generate reason for each candidate
            for c in filtered:
                scores = RecommendationScorer.score_candidate(
                    candidate=c,
                    gap_comp_code=gap.competency_code,
                    gap_comp_name=gap.competency_name,
                    required_level=gap.required_level,
                    current_level=gap.current_level,
                    weights=weights
                )
                
                reason = RankingService.generate_explanation(
                    candidate=c,
                    comp_name=gap.competency_name,
                    current_level=gap.current_level,
                    required_level=gap.required_level
                )
                
                scored_candidates.append({
                    "candidate": c,
                    "scores": scores,
                    "competency_id": comp_id,
                    "competency_code": gap.competency_code,
                    "gap_size": gap.gap,
                    "reason": reason
                })
                
        # 5. Rank and persist to Database (returns SQLAlchemy objects)
        return RankingService.rank_and_persist(db, user_id, scored_candidates)

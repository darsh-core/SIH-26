from typing import Dict
from pydantic import BaseModel

from app.services.recommendation.candidate_retriever import RecommendationCandidate
from app.services.recommendation.semantic_scorer import MockSemanticScorer

class RecommendationWeights(BaseModel):
    competency_match: float = 0.40
    semantic_similarity: float = 0.20
    difficulty_fit: float = 0.15
    duration_fit: float = 0.10
    provider_quality: float = 0.10
    recency: float = 0.05

# DEMO/SYNTHETIC quality scores
PROVIDER_QUALITY_SCORES = {
    "iGOT": 0.85,
    "NSSTA": 0.95
}

class RecommendationScorer:
    
    @staticmethod
    def score_candidate(
        candidate: RecommendationCandidate,
        gap_comp_code: str,
        gap_comp_name: str,
        required_level: float,
        current_level: float,
        weights: RecommendationWeights = RecommendationWeights()
    ) -> Dict[str, float]:
        """
        Calculates individual scoring dimensions and the final weighted score (0-100) for a candidate.
        """
        gap_size = max(0.0, required_level - current_level)
        
        # 1. Competency Match
        comp_mapping = next((m for m in candidate.competency_mappings if m.competency_code == gap_comp_code), None)
        if not comp_mapping:
            comp_match = 0.0
        else:
            # High score if it maps to target, with level matching:
            # If target level targets the required level, high score
            level_diff = abs(comp_mapping.target_level - required_level)
            level_factor = max(0.1, 1.0 - (level_diff * 0.2))
            comp_match = comp_mapping.weight * level_factor
            
        # 2. Difficulty Fit
        # Map current competency level to appropriate resource difficulty
        diff_lower = candidate.difficulty.lower()
        if current_level < 2.0:  # Beginner needs basic courses
            if "beginner" in diff_lower or "basic" in diff_lower:
                diff_fit = 1.0
            elif "intermediate" in diff_lower:
                diff_fit = 0.6
            else:
                diff_fit = 0.2
        elif current_level < 3.5:  # Intermediate needs intermediate/advanced
            if "intermediate" in diff_lower:
                diff_fit = 1.0
            elif "advanced" in diff_lower or "expert" in diff_lower:
                diff_fit = 0.8
            else:
                diff_fit = 0.4
        else:  # Advanced needs advanced
            if "advanced" in diff_lower or "expert" in diff_lower:
                diff_fit = 1.0
            elif "intermediate" in diff_lower:
                diff_fit = 0.5
            else:
                diff_fit = 0.1
                
        # 3. Duration Fit
        # Large gaps (gap >= 1.5) require longer comprehensive learning paths
        # Small gaps can be covered by quick learning modules
        dur = candidate.duration_minutes
        if gap_size >= 1.5:
            # Prefer longer resources (e.g. >= 240 minutes)
            if dur >= 240:
                dur_fit = 1.0
            else:
                # Shorter courses get lesser score for large gaps (but still positive)
                dur_fit = 0.6
        else:
            # Prefer shorter, specific courses
            if dur <= 240:
                dur_fit = 1.0
            elif dur <= 480:
                dur_fit = 0.7
            else:
                dur_fit = 0.3
                
        # 4. Semantic Similarity
        text_for_semantic = f"{candidate.title} {candidate.description or ''}"
        scorer = MockSemanticScorer()
        semantic_similarity = scorer.calculate_similarity(text_for_semantic, gap_comp_name)
        
        # 5. Provider Quality
        provider_quality = PROVIDER_QUALITY_SCORES.get(candidate.provider, 0.80)
        
        # 6. Recency
        # Newer content gets a slight boost. Synthetic date boost default to neutral
        recency = 0.80
        
        # Calculate final weighted score (range 0.0 to 1.0)
        raw_score = (
            (comp_match * weights.competency_match) +
            (semantic_similarity * weights.semantic_similarity) +
            (diff_fit * weights.difficulty_fit) +
            (dur_fit * weights.duration_fit) +
            (provider_quality * weights.provider_quality) +
            (recency * weights.recency)
        )
        
        # Normalize to 0-100 range
        normalized_score = round(raw_score * 100.0, 1)
        
        return {
            "competency_match": round(comp_match, 2),
            "semantic_similarity": round(semantic_similarity, 2),
            "difficulty_fit": round(diff_fit, 2),
            "duration_fit": round(dur_fit, 2),
            "provider_quality": round(provider_quality, 2),
            "recency": round(recency, 2),
            "raw_score": round(raw_score, 4),
            "final_score": normalized_score
        }

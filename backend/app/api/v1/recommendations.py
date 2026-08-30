import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser, UserProfile
from app.models.competency import Competency
from app.services.recommendation_service import RecommendationService
from app.services.gap_engine import GapEngine
from app.services.recommendation.recommendation_scorer import RecommendationScorer
from app.services.recommendation.candidate_retriever import CandidateRetriever
from app.schemas.recommendation import (
    PersonalizedRecommendationResponse,
    PersonalizedItemResponse,
    TargetCompetencyDetail
)

router = APIRouter(tags=["Recommendations"])

@router.get("/users/{user_id}/recommendations", response_model=PersonalizedRecommendationResponse, summary="Get Personalized Recommendations")
def get_user_recommendations(
    user_id: uuid.UUID,
    priority: Optional[str] = Query(None, description="Filter by gap priority (HIGH, MEDIUM, LOW)"),
    provider: Optional[str] = Query(None, description="Filter by provider (iGOT, NSSTA)"),
    competency: Optional[str] = Query(None, description="Filter by competency code"),
    limit: int = Query(10, ge=1),
    debug: bool = Query(False, description="Expose internal scoring breakdown (Admins/Managers only)"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    # Authorization
    if not current_user.is_superuser and current_user.id != user_id:
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: cannot view recommendations of other users"
            )

    # 1. Fetch recommendations (will generate if not persisted)
    recs = RecommendationService.get_recommendations(db, user_id=user_id)
    
    # 2. Fetch gap engine metrics to populate current/target levels and readiness
    gap_data = GapEngine.calculate_gaps(db, user_id=user_id)
    overall_readiness = gap_data.overall_readiness
    
    gap_map = {g.competency_code: g for g in gap_data.gaps}
    
    # Get user profile designation/role name
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    role_name = profile.designation if profile and profile.designation else "Official"

    # 3. Process and filter recommendations
    items = []
    for r in recs:
        # Resolve target competency details
        comp_code = r.competency.code
        gap_info = gap_map.get(comp_code)
        
        # Priority Filter
        item_priority = gap_info.priority if gap_info else "NONE"
        if priority and item_priority.upper() != priority.upper():
            continue
            
        # Provider Filter
        item_provider = "iGOT" if r.item_type == "COURSE" else "NSSTA"
        if provider and item_provider.upper() != provider.upper():
            continue
            
        # Competency Code Filter
        if competency and comp_code.upper() != competency.upper():
            continue
            
        # Build target competency details block
        t_comp = TargetCompetencyDetail(
            code=comp_code,
            current_level=gap_info.current_level if gap_info else 0.0,
            required_level=gap_info.required_level if gap_info else 0.0,
            gap=gap_info.gap if gap_info else 0.0
        )
        
        # Populate resource metadata
        title = r.course.title if r.item_type == "COURSE" else r.training_program.title
        difficulty = r.course.difficulty if r.item_type == "COURSE" else "Intermediate"
        duration = r.course.duration_minutes if r.item_type == "COURSE" else (r.training_program.duration_days * 8 * 60)
        resource_id = r.course_id if r.item_type == "COURSE" else r.training_program_id

        # Calculate on-the-fly debug scores if requested
        debug_scores = None
        if debug:
            # We can recompute the score values for the response
            # Construct mock candidate
            from app.services.recommendation.candidate_retriever import RecommendationCandidate, CandidateMapping
            c_mappings = [CandidateMapping(competency_code=comp_code, target_level=int(gap_info.required_level if gap_info else 1), weight=1.0)]
            c = RecommendationCandidate(
                code=r.course.code if r.item_type == "COURSE" else r.training_program.code,
                title=title,
                description=r.course.description if r.item_type == "COURSE" else r.training_program.description,
                provider=item_provider,
                difficulty=difficulty,
                language="English",
                duration_minutes=duration,
                mode="ONLINE" if r.item_type == "COURSE" else "OFFLINE",
                competency_mappings=c_mappings
            )
            debug_scores = RecommendationScorer.score_candidate(
                candidate=c,
                gap_comp_code=comp_code,
                gap_comp_name=r.competency.name,
                required_level=gap_info.required_level if gap_info else 0.0,
                current_level=gap_info.current_level if gap_info else 0.0
            )

        items.append(
            PersonalizedItemResponse(
                resource_id=resource_id,
                provider=item_provider,
                title=title,
                resource_type=r.item_type,
                target_competencies=[t_comp],
                score=r.recommendation_score,
                priority=item_priority,
                reason=r.logic_explanation,
                estimated_duration_minutes=duration,
                difficulty=difficulty,
                debug_scores=debug_scores
            )
        )

    # Sort descending by score and limit
    items = sorted(items, key=lambda x: x.score, reverse=True)[:limit]
    
    return PersonalizedRecommendationResponse(
        user_id=user_id,
        role=role_name,
        overall_readiness=overall_readiness,
        recommendations=items
    )


@router.post("/users/{user_id}/recommendations/refresh", response_model=PersonalizedRecommendationResponse, summary="Refresh Recommendations")
def refresh_user_recommendations(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    if not current_user.is_superuser and current_user.id != user_id:
        user_role_names = [role.name for role in current_user.roles]
        if "SUPERVISOR" not in user_role_names and "MANAGER" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
            
    # Force recalculation and persistence
    RecommendationService.generate_recommendations(db, user_id=user_id)
    
    # Return recommendations
    return get_user_recommendations(
        user_id=user_id,
        priority=None,
        provider=None,
        competency=None,
        limit=10,
        debug=False,
        db=db,
        current_user=current_user
    )


# For legacy endpoint integration and compatibility
@router.get("/recommendations", response_model=List[PersonalizedItemResponse], summary="List Legacy Recommendations for Current User")
def list_legacy_recommendations(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    resp = get_user_recommendations(
        user_id=current_user.id,
        priority=None,
        provider=None,
        competency=None,
        limit=10,
        debug=False,
        db=db,
        current_user=current_user
    )
    return resp.recommendations

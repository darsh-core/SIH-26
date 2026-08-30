import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import AppUser, UserProfile, Organization, RBACRole
from app.models.competency import CompetencyFramework, Competency, CompetencyLevel, JobRole, RoleCompetency, UserCompetency, CompetencyEvidence
from app.models.course import Course, TrainingProgram, LearningProgress, Provider
from app.models.recommendation import Recommendation, LearningPlan
from app.services.recommendation import CandidateRetriever, EligibilityFilter, RecommendationScorer, RecommendationWeights, RankingService
from app.services.recommendation_service import RecommendationService
from app.core.security import get_password_hash

@pytest.fixture
def setup_recommendation_data(db_session: Session):
    # Recreate default Organization
    org = Organization(name="Test MoSPI", code="TEST_MOSPI")
    db_session.add(org)
    
    # Create System Roles
    official_role = RBACRole(name="OFFICIAL", description="Staff")
    db_session.add(official_role)
    
    # Create Framework and Competencies
    fw = CompetencyFramework(name="STATISTICAL", description="Framework")
    db_session.add(fw)
    db_session.flush()
    
    sampling = Competency(framework_id=fw.id, name="Sampling Methodology", code="STAT_SAMPLING", description="Sampling")
    survey = Competency(framework_id=fw.id, name="Survey Design", code="STAT_SURVEY_DESIGN", description="Survey")
    db_session.add_all([sampling, survey])
    db_session.flush()
    
    # Create Job Role
    job_role = JobRole(name="Statistical Officer", code="ROLE_STAT_OFFICER", description="SO Role")
    db_session.add(job_role)
    db_session.flush()
    
    # Map required levels:
    # Sampling: required=4, weight=1.0, mandatory=True
    # Survey Design: required=3, weight=0.5, mandatory=False
    rc_sampling = RoleCompetency(
        job_role_id=job_role.id,
        competency_id=sampling.id,
        required_level=4,
        weight=1.0,
        is_mandatory=True
    )
    rc_survey = RoleCompetency(
        job_role_id=job_role.id,
        competency_id=survey.id,
        required_level=3,
        weight=0.5,
        is_mandatory=False
    )
    db_session.add_all([rc_sampling, rc_survey])
    db_session.flush()
    
    # Create User Ramesh
    user = AppUser(email="ramesh@test.gov.in", hashed_password=get_password_hash("password123"), is_active=True)
    user.roles.append(official_role)
    db_session.add(user)
    db_session.flush()
    
    profile = UserProfile(
        user_id=user.id,
        first_name="Ramesh",
        last_name="Chandra",
        designation="Statistical Officer",
        department="Field Surveys",
        job_role_id=job_role.id
    )
    db_session.add(profile)
    
    # Seed current levels: Sampling = 2.3, Survey Design = 3.5
    uc_sampling = UserCompetency(user_id=user.id, competency_id=sampling.id, current_level=2.3, status="EVALUATED")
    uc_survey = UserCompetency(user_id=user.id, competency_id=survey.id, current_level=3.5, status="EVALUATED")
    db_session.add_all([uc_sampling, uc_survey])
    db_session.flush()
    
    # Seed Providers in DB
    igot_provider = Provider(name="iGOT Karmayogi", description="iGOT", status="ACTIVE")
    nssta_provider = Provider(name="National Statistical Systems Training Academy (NSSTA)", description="NSSTA", status="ACTIVE")
    db_session.add_all([igot_provider, nssta_provider])
    db_session.flush()
    
    # Seed Course in DB
    c1 = Course(
        provider_id=igot_provider.id,
        code="IGOT_COMP_STATS_03",
        title="Sampling Techniques for Household Surveys",
        description="Sampling basic",
        duration_minutes=240,
        difficulty="Intermediate",
        language="Hindi"
    )
    c2 = Course(
        provider_id=igot_provider.id,
        code="IGOT_COMP_STATS_04",
        title="Advanced Probability Sampling Methods",
        description="Advanced sampling",
        duration_minutes=240,
        difficulty="Advanced",
        language="English"
    )
    db_session.add_all([c1, c2])
    db_session.flush()
    
    # Seed Training Program in DB
    tp = TrainingProgram(
        provider_id=nssta_provider.id,
        code="NSSTA_PROG_STATS_01",
        title="Professional Training on Sampling Design & Estimation Methods",
        description="Intensive hands-on sampling",
        duration_days=10,
        mode="OFFLINE"
    )
    db_session.add(tp)
    db_session.flush()
    
    db_session.commit()
    
    return {
        "user_id": user.id,
        "sampling_id": sampling.id,
        "survey_id": survey.id,
        "job_role_id": job_role.id,
        "igot_provider_id": igot_provider.id,
        "c1_id": c1.id,
        "c2_id": c2.id,
        "tp_id": tp.id
    }


def test_candidate_retrieval_and_provider_abstraction(setup_recommendation_data):
    # Retrieve candidates addressing STAT_SAMPLING
    candidates = CandidateRetriever.retrieve_candidates(["STAT_SAMPLING"])
    
    assert len(candidates) > 0
    # Must retrieve both iGOT course and NSSTA program
    assert any(c.provider == "iGOT" for c in candidates)
    assert any(c.provider == "NSSTA" for c in candidates)
    
    # Check normalized properties
    igot_cand = next(c for c in candidates if c.provider == "iGOT" and c.code == "IGOT_COMP_STATS_03")
    assert igot_cand.difficulty == "Intermediate"
    assert igot_cand.duration_minutes == 240
    
    nssta_cand = next(c for c in candidates if c.provider == "NSSTA" and c.code == "NSSTA_PROG_STATS_01")
    # Normalized duration: 10 days * 8 hours/day * 60 minutes = 4800 minutes
    assert nssta_cand.duration_minutes == 4800


def test_eligibility_filtering(db_session: Session, setup_recommendation_data):
    user_id = setup_recommendation_data["user_id"]
    c1_id = setup_recommendation_data["c1_id"]
    c2_id = setup_recommendation_data["c2_id"]
    
    candidates = CandidateRetriever.retrieve_candidates(["STAT_SAMPLING"])
    
    current_levels = {"STAT_SAMPLING": 2.3}
    target_levels = {"STAT_SAMPLING": 4.0}
    
    # 1. Filter initially (all should pass)
    filtered = EligibilityFilter.filter_candidates(
        db_session, user_id, candidates, current_levels, target_levels
    )
    assert len(filtered) == len(candidates)
    
    # 2. Add completion history (completed c1)
    progress = LearningProgress(
        user_id=user_id,
        item_type="COURSE",
        course_id=c1_id,
        progress_percentage=100.0,
        status="COMPLETED"
    )
    db_session.add(progress)
    db_session.commit()
    
    # Filter again (c1 should be excluded)
    filtered_completed = EligibilityFilter.filter_candidates(
        db_session, user_id, candidates, current_levels, target_levels
    )
    assert not any(c.code == "IGOT_COMP_STATS_03" for c in filtered_completed)


def test_recommendation_scorer_math(setup_recommendation_data):
    candidates = CandidateRetriever.retrieve_candidates(["STAT_SAMPLING"])
    c_advanced = next(c for c in candidates if c.code == "IGOT_COMP_STATS_04")
    
    # Calculate score manually:
    # Target level = 4.0. Gap = 1.7. Current level = 2.3.
    # weights: comp=40%, semantic=20%, difficulty=15%, duration=10%, quality=10%, recency=5%
    scores = RecommendationScorer.score_candidate(
        candidate=c_advanced,
        gap_comp_code="STAT_SAMPLING",
        gap_comp_name="Sampling Methodology",
        required_level=4.0,
        current_level=2.3
    )
    
    # Final score should be valid normalized float between 0 and 100
    assert 0.0 <= scores["final_score"] <= 100.0
    assert "competency_match" in scores
    assert "difficulty_fit" in scores
    assert "duration_fit" in scores


def test_ranking_and_explainability(db_session: Session, setup_recommendation_data):
    user_id = setup_recommendation_data["user_id"]
    sampling_id = setup_recommendation_data["sampling_id"]
    
    # Get candidates
    candidates = CandidateRetriever.retrieve_candidates(["STAT_SAMPLING"])
    
    # Prepare list for ranking
    scored_candidates = []
    for c in candidates:
        scores = RecommendationScorer.score_candidate(
            candidate=c,
            gap_comp_code="STAT_SAMPLING",
            gap_comp_name="Sampling Methodology",
            required_level=4.0,
            current_level=2.3
        )
        reason = RankingService.generate_explanation(c, "Sampling Methodology", 2.3, 4.0)
        
        scored_candidates.append({
            "candidate": c,
            "scores": scores,
            "competency_id": sampling_id,
            "competency_code": "STAT_SAMPLING",
            "gap_size": 1.7,
            "reason": reason
        })
        
    # Rank and persist
    persisted = RankingService.rank_and_persist(db_session, user_id, scored_candidates)
    
    # Verification
    assert len(persisted) > 0
    # First item must have the highest recommendation_score
    assert persisted[0].recommendation_score >= persisted[-1].recommendation_score
    # Logic explanation must not be empty
    assert persisted[0].logic_explanation != ""
    assert "Sampling" in persisted[0].logic_explanation


def test_adaptive_recommendation_flow(db_session: Session, setup_recommendation_data):
    user_id = setup_recommendation_data["user_id"]
    sampling_id = setup_recommendation_data["sampling_id"]
    
    # 1. User level = 2.3. required = 4.0. Gap = 1.7 (large gap)
    # Generate recommendations
    recs_before = RecommendationService.generate_recommendations(db_session, user_id=user_id)
    
    # Find active recommendations for Sampling
    sampling_recs_before = [r for r in recs_before if r.competency_id == sampling_id]
    
    # The advanced course (IGOT_COMP_STATS_04) should be recommended and rank high
    c4_before = next((r for r in sampling_recs_before if r.course and r.course.code == "IGOT_COMP_STATS_04"), None)
    assert c4_before is not None
    
    # 2. Update user level to 3.8. Gap = 0.2 (minor gap, close to target)
    uc_sampling = db_session.query(UserCompetency).filter(
        UserCompetency.user_id == user_id,
        UserCompetency.competency_id == sampling_id
    ).first()
    uc_sampling.current_level = 3.8
    db_session.commit()
    
    # Recalculate recommendations
    recs_after = RecommendationService.generate_recommendations(db_session, user_id=user_id)
    sampling_recs_after = [r for r in recs_after if r.competency_id == sampling_id]
    
    # Advanced course targets level 4, which is appropriate. But beginner/intermediate techniques course (IGOT_COMP_STATS_03 targets level 2)
    # should be deprioritized or filtered since user is at 3.8!
    # Let's verify that the ranking of the resources changed
    # (Since current_level is 3.8, course targeting level 2 has target < current - 1, which means it will be filtered out!)
    # Let's assert that IGOT_COMP_STATS_03 is filtered out of the list entirely!
    assert not any(r.course and r.course.code == "IGOT_COMP_STATS_03" for r in sampling_recs_after)


def test_api_recommendation_endpoints(client: TestClient, setup_recommendation_data):
    user_id = setup_recommendation_data["user_id"]
    sampling_id = setup_recommendation_data["sampling_id"]
    
    # 1. Login Ramesh
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "password123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get recommendations via API
    rec_resp = client.get(f"/api/v1/users/{user_id}/recommendations", headers=headers)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["user_id"] == str(user_id)
    assert "role" in rec_data
    assert len(rec_data["recommendations"]) > 0
    
    # Check course detail format
    first_item = rec_data["recommendations"][0]
    assert "resource_id" in first_item
    assert "provider" in first_item
    assert "score" in first_item
    assert first_item["priority"] in ["HIGH", "MEDIUM", "LOW", "NONE"]
    
    # 3. Refresh recommendations via API
    refresh_resp = client.post(f"/api/v1/users/{user_id}/recommendations/refresh", headers=headers)
    assert refresh_resp.status_code == 200
    assert len(refresh_resp.json()["recommendations"]) > 0
    
    # 4. Get competency-specific recommendations via API
    comp_rec_resp = client.get(f"/api/v1/users/{user_id}/competencies/{sampling_id}/recommendations", headers=headers)
    assert comp_rec_resp.status_code == 200
    assert len(comp_rec_resp.json()) > 0
    
    # 5. Generate learning plan via API
    plan_gen_resp = client.post(f"/api/v1/users/{user_id}/learning-plans/generate", headers=headers)
    assert plan_gen_resp.status_code == 201
    plan_data = plan_gen_resp.json()
    plan_id = plan_data["id"]
    assert plan_data["user_id"] == str(user_id)
    assert len(plan_data["items"]) > 0
    
    # 6. List learning plans
    list_plans_resp = client.get(f"/api/v1/users/{user_id}/learning-plans", headers=headers)
    assert list_plans_resp.status_code == 200
    assert len(list_plans_resp.json()) > 0
    
    # 7. Get specific learning plan
    get_plan_resp = client.get(f"/api/v1/learning-plans/{plan_id}", headers=headers)
    assert get_plan_resp.status_code == 200
    assert get_plan_resp.json()["title"] == "Personalized Skill Development Plan"
    
    # 8. Remove plan item
    item_id = plan_data["items"][0]["id"]
    del_resp = client.delete(f"/api/v1/learning-plans/{plan_id}/items/{item_id}", headers=headers)
    assert del_resp.status_code == 204
    
    # Verify item is removed
    get_plan_resp_after = client.get(f"/api/v1/learning-plans/{plan_id}", headers=headers)
    assert get_plan_resp_after.status_code == 200
    assert len(get_plan_resp_after.json()["items"]) == len(plan_data["items"]) - 1

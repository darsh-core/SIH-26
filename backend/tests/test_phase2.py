import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.user import AppUser, Organization, RBACRole, UserProfile
from app.models.competency import CompetencyFramework, Competency, CompetencyLevel, JobRole, RoleCompetency, UserCompetency, CompetencyEvidence
from app.models.assessment import Assessment, Question, QuestionOption, QuestionCompetency, AssessmentAttempt, AttemptAnswer
from app.services.gap_engine import GapEngine

@pytest.fixture
def setup_sih_data(db_session: Session):
    # Create default Organization
    org = Organization(name="Test MoSPI Office", code="TEST_MOSPI")
    db_session.add(org)
    
    # Create RBAC Roles
    admin_role = RBACRole(name="ADMIN", description="Admin privilege")
    official_role = RBACRole(name="OFFICIAL", description="Standard staff")
    db_session.add_all([admin_role, official_role])
    
    # Create Competency Framework
    fw = CompetencyFramework(name="STATISTICAL", description="Statistical competencies")
    db_session.add(fw)
    db_session.flush()
    
    # Create Competencies
    sampling = Competency(
        framework_id=fw.id,
        name="Sampling Design",
        code="STAT_SAMPLING",
        description="Sampling techniques"
    )
    survey_design = Competency(
        framework_id=fw.id,
        name="Survey Design",
        code="STAT_SURVEY_DESIGN",
        description="Survey blueprints"
    )
    db_session.add_all([sampling, survey_design])
    db_session.flush()
    
    # Create Level 1-5 definitions for Sampling
    for i in range(1, 6):
        db_session.add(CompetencyLevel(
            competency_id=sampling.id,
            level=i,
            name=f"Level {i}",
            description=f"Sampling Level {i} description",
            behavior_indicators=[f"Indicator {i}"]
        ))
    db_session.flush()
    
    # Create Job Role
    job_role = JobRole(
        name="Statistical Officer",
        code="ROLE_STAT_OFFICER",
        description="Officer role"
    )
    db_session.add(job_role)
    db_session.flush()
    
    # Map required competencies:
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
        competency_id=survey_design.id,
        required_level=3,
        weight=0.5,
        is_mandatory=False
    )
    db_session.add_all([rc_sampling, rc_survey])
    
    # Create Admin User
    admin_user = AppUser(
        email="admin@test.gov.in",
        hashed_password=get_password_hash("adminpwd123"),
        is_active=True,
        is_superuser=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    
    # Create Demo User Ramesh
    user = AppUser(
        email="ramesh@test.gov.in",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False,
        organization_id=org.id
    )
    user.roles.append(official_role)
    db_session.add(user)
    db_session.flush()
    
    profile = UserProfile(
        user_id=user.id,
        first_name="Ramesh",
        last_name="Chandra",
        designation="Statistical Officer",
        department="Field Surveys Division",
        job_role_id=job_role.id
    )
    db_session.add(profile)
    
    # Seed current levels:
    # Sampling: current=2.0 (Required=4, Gap=2.0)
    # Survey Design: current=5.0 (Required=3, Gap=0.0)
    uc_sampling = UserCompetency(
        user_id=user.id,
        competency_id=sampling.id,
        current_level=2.0,
        status="EVALUATED"
    )
    uc_survey = UserCompetency(
        user_id=user.id,
        competency_id=survey_design.id,
        current_level=5.0,
        status="EVALUATED"
    )
    db_session.add_all([uc_sampling, uc_survey])
    
    # Create Assessment
    assessment = Assessment(
        title="Sampling Core Test",
        description="Sampling evaluation",
        pass_percentage=50.0,
        is_ai_generated=False
    )
    db_session.add(assessment)
    db_session.flush()
    
    q1 = Question(
        assessment_id=assessment.id,
        text="Sample Question 1",
        difficulty="Medium",
        explanation="Standard explanation"
    )
    db_session.add(q1)
    db_session.flush()
    
    opt1 = QuestionOption(question_id=q1.id, text="Correct Option", is_correct=True)
    opt2 = QuestionOption(question_id=q1.id, text="Wrong Option", is_correct=False)
    db_session.add_all([opt1, opt2])
    
    # Map question to Sampling Level 4
    qc1 = QuestionCompetency(question_id=q1.id, competency_id=sampling.id, target_level=4, weight=1.0)
    db_session.add(qc1)
    
    db_session.commit()
    
    return {
        "user_id": user.id,
        "admin_id": admin_user.id,
        "sampling_id": sampling.id,
        "survey_id": survey_design.id,
        "job_role_id": job_role.id,
        "assessment_id": assessment.id,
        "question_id": q1.id,
        "correct_option_id": opt1.id,
        "wrong_option_id": opt2.id
    }


def test_auth_endpoints(client: TestClient, setup_sih_data):
    # 1. Login success
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "password123"}
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    # 2. Login invalid password
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
    # 3. GET /auth/me authenticated
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "ramesh@test.gov.in"
    
    # 4. RBAC check: non-admin tries to view user list (returns 403)
    users_resp = client.get("/api/v1/users", headers=headers)
    assert users_resp.status_code == 403


def test_gap_engine_math_logic(db_session: Session, setup_sih_data):
    user_id = setup_sih_data["user_id"]
    
    # Trigger gap engine
    gaps_response = GapEngine.calculate_gaps(db_session, user_id)
    
    # Verify Sampling: required=4, current=2 -> gap=2, priority="HIGH"
    sampling_gap = next(g for g in gaps_response.gaps if g.competency_code == "STAT_SAMPLING")
    assert sampling_gap.gap == 2.0
    assert sampling_gap.normalized_gap == 0.5
    assert sampling_gap.priority == "HIGH"
    
    # Verify Survey Design: required=3, current=5 -> gap=0, priority="NONE"
    survey_gap = next(g for g in gaps_response.gaps if g.competency_code == "STAT_SURVEY_DESIGN")
    assert survey_gap.gap == 0.0
    assert survey_gap.priority == "NONE"
    
    # Verify Weighted Readiness calculations:
    # Sampling: current/required = 2/4 = 0.5. weight = 1.0. contribution = 0.5 * 1.0 = 0.5
    # Survey Design: current/required = 5/3 = 1.67 -> min(1.67, 1.0) = 1.0. weight = 0.5. contribution = 1.0 * 0.5 = 0.5
    # Total contribution = 0.5 + 0.5 = 1.0
    # Total weights = 1.0 + 0.5 = 1.5
    # Readiness = 1.0 / 1.5 * 100 = 66.666% -> rounded to 66.7%
    assert gaps_response.overall_readiness == 66.7


def test_gap_api_endpoint(client: TestClient, setup_sih_data):
    user_id = setup_sih_data["user_id"]
    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # GET /users/{user_id}/competency-gaps
    response = client.get(f"/api/v1/users/{user_id}/competency-gaps", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["overall_readiness"] == 66.7
    assert len(res_data["gaps"]) == 2


def test_assessment_submission_loop(client: TestClient, setup_sih_data):
    user_id = setup_sih_data["user_id"]
    assess_id = setup_sih_data["assessment_id"]
    q1_id = setup_sih_data["question_id"]
    correct_opt_id = setup_sih_data["correct_option_id"]
    
    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Start Assessment Attempt
    start_resp = client.post(f"/api/v1/assessments/{assess_id}/start", headers=headers)
    assert start_resp.status_code == 200
    attempt_data = start_resp.json()
    attempt_id = attempt_data["attempt_id"]
    assert len(attempt_data["questions"]) == 1
    
    # 2. Submit Correct Option
    submit_resp = client.post(
        f"/api/v1/assessments/{assess_id}/submit?attempt_id={attempt_id}",
        json={
            "answers": [
                {"question_id": str(q1_id), "selected_option_id": str(correct_opt_id)}
            ]
        },
        headers=headers
    )
    assert submit_resp.status_code == 200
    res_data = submit_resp.json()
    assert res_data["score"] == 100.0
    assert res_data["is_passed"] is True
    
    # Verify User Competency Level upgrade feedback loop
    # Target level was 4. Accuracy was 100%. Gain = 4 * 1.0 = 4.0.
    # Current level was 2.0. New level = max(2.0, 4.0) = 4.0.
    # Check current competencies endpoint
    comp_resp = client.get(f"/api/v1/users/{user_id}/competencies", headers=headers)
    assert comp_resp.status_code == 200
    sampling_comp = next(c for c in comp_resp.json() if c["competency_code"] == "STAT_SAMPLING")
    assert sampling_comp["current_level"] == 4.0
    
    # Verify competency evidence was created
    evidence_resp = client.get(f"/api/v1/users/{user_id}/evidence", headers=headers)
    assert evidence_resp.status_code == 200
    assert len(evidence_resp.json()) == 1
    assert "Assessed via" in evidence_resp.json()[0]["description"]
    
    # Verify gap recalculation (Sampling current is now 4.0, gap becomes 0.0)
    gap_resp = client.get(f"/api/v1/users/{user_id}/competency-gaps", headers=headers)
    assert gap_resp.status_code == 200
    gaps_data = gap_resp.json()
    sampling_gap = next(g for g in gaps_data["gaps"] if g["competency_code"] == "STAT_SAMPLING")
    assert sampling_gap["gap"] == 0.0
    # Readiness should update to 100% since both competencies are fully met (Sampling: 4/4=1, Survey: 5/3=1.67->1)
    assert gaps_data["overall_readiness"] == 100.0

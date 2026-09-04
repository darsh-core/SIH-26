import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import AppUser, UserProfile, Organization, RBACRole
from app.models.competency import CompetencyFramework, Competency, JobRole, RoleCompetency, UserCompetency
from app.models.course import Course, Provider
from app.models.recommendation import Recommendation
from app.core.security import get_password_hash, create_access_token
from app.main import app

@pytest.fixture
def copilot_test_user(db_session: Session):
    # Setup test org and roles
    org = db_session.query(Organization).filter_by(code="TEST_MOSPI_COPILOT").first()
    if not org:
        org = Organization(name="Test MoSPI Copilot", code="TEST_MOSPI_COPILOT")
        db_session.add(org)
        db_session.flush()
    
    role = db_session.query(RBACRole).filter_by(name="OFFICIAL").first()
    if not role:
        role = RBACRole(name="OFFICIAL", description="Staff")
        db_session.add(role)
        db_session.flush()

    fw = db_session.query(CompetencyFramework).filter_by(name="STATISTICAL").first()
    if not fw:
        fw = CompetencyFramework(name="STATISTICAL", description="Framework")
        db_session.add(fw)
        db_session.flush()

    sampling = db_session.query(Competency).filter_by(code="STAT_SAMPLING").first()
    if not sampling:
        sampling = Competency(framework_id=fw.id, name="Sampling Methodology", code="STAT_SAMPLING", description="Sampling")
        db_session.add(sampling)
    
    cpi = db_session.query(Competency).filter_by(code="STAT_CPI").first()
    if not cpi:
        cpi = Competency(framework_id=fw.id, name="Consumer Price Index", code="STAT_CPI", description="CPI")
        db_session.add(cpi)
    db_session.flush()

    job_role = db_session.query(JobRole).filter_by(code="ROLE_STAT_OFFICER").first()
    if not job_role:
        job_role = JobRole(name="Statistical Officer", code="ROLE_STAT_OFFICER", description="SO Role")
        db_session.add(job_role)
        db_session.flush()

    # Role requirements: Sampling required=4.0, CPI required=3.5
    rc1 = db_session.query(RoleCompetency).filter_by(job_role_id=job_role.id, competency_id=sampling.id).first()
    if not rc1:
        rc1 = RoleCompetency(job_role_id=job_role.id, competency_id=sampling.id, required_level=4.0, weight=1.5, is_mandatory=True)
        db_session.add(rc1)
    rc2 = db_session.query(RoleCompetency).filter_by(job_role_id=job_role.id, competency_id=cpi.id).first()
    if not rc2:
        rc2 = RoleCompetency(job_role_id=job_role.id, competency_id=cpi.id, required_level=3.5, weight=1.0, is_mandatory=False)
        db_session.add(rc2)
    db_session.flush()

    # User
    user = db_session.query(AppUser).filter_by(email="copilot_learner@mospi.gov.in").first()
    if not user:
        user = AppUser(
            email="copilot_learner@mospi.gov.in",
            hashed_password=get_password_hash("password123"),
            organization_id=org.id,
            is_active=True
        )
        user.roles.append(role)
        db_session.add(user)
        db_session.flush()

        profile = UserProfile(
            user_id=user.id,
            first_name="Ramesh",
            last_name="Singh",
            designation="Senior Field Investigator",
            department="Field Operations Division",
            job_role_id=job_role.id
        )
        db_session.add(profile)

        # User assessed competencies: Sampling=2.0 (gap=2.0), CPI=2.5 (gap=1.0)
        uc1 = UserCompetency(user_id=user.id, competency_id=sampling.id, current_level=2.0, status="EVALUATED")
        uc2 = UserCompetency(user_id=user.id, competency_id=cpi.id, current_level=2.5, status="EVALUATED")
        db_session.add_all([uc1, uc2])

        # Courses & Recommendations
        prov = db_session.query(Provider).filter_by(name="iGOT Karmayogi").first()
        if not prov:
            prov = Provider(name="iGOT Karmayogi")
            db_session.add(prov)
            db_session.flush()

        course = Course(
            title="Advanced Stratified Sampling in NSS Surveys",
            code="CRS_SAMP_01",
            provider_id=prov.id,
            description="Comprehensive course on stratified random sampling.",
            difficulty="Intermediate",
            duration_minutes=120
        )
        db_session.add(course)
        db_session.flush()

        rec = Recommendation(
            user_id=user.id,
            item_type="COURSE",
            course_id=course.id,
            competency_id=sampling.id,
            gap_score=2,
            recommendation_score=94.5,
            logic_explanation="Directly bridges the 2.0 level deficit in Sampling Methodology for Statistical Officer cadre.",
            confidence_score=0.92,
            status="PENDING"
        )
        db_session.add(rec)
        db_session.flush()

    return user

def test_quick_prompts_endpoint(client: TestClient):
    resp = client.get("/api/v1/copilot/quick-prompts")
    assert resp.status_code == 200
    prompts = resp.json()
    assert len(prompts) >= 5
    titles = [p["title"] for p in prompts]
    assert "Analyze My Skill Gaps" in titles
    assert "Recommended Learning & Why" in titles

def test_copilot_realtime_freeform_qa(client: TestClient):
    resp = client.post(
        "/api/v1/copilot/chat",
        json={"message": "What is the primary advantage of stratified sampling?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    # Must not be raw JSON string
    assert not data["reply"].startswith('{"Heading"')

def test_copilot_with_authenticated_user_context(client: TestClient, copilot_test_user: AppUser):
    token = create_access_token({"sub": copilot_test_user.email})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Analyze my skill gaps and recommend what course I should take, and why you suggest that."},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    reply = data["reply"]
    assert len(reply) > 50
    # Verify skill gap or recommendation context was considered
    assert "Sampling" in reply or "competency" in reply.lower() or "gap" in reply.lower()

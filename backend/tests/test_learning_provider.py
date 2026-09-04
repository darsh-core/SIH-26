import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.course import Course, CourseModule, LearningProgress
from app.models.user import AppUser
from app.integrations.learning_provider import (
    get_learning_provider,
    DemoIGOTProvider,
    IGOTProvider,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def auth_headers(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "employee@mospi.gov.in", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def sample_course(db):
    course = db.query(Course).filter(Course.code == "IGOT_COMP_STATS_01").first()
    if not course:
        course = db.query(Course).first()
    assert course is not None, "At least one course must be seeded"
    return course


def test_provider_factory_switching(monkeypatch):
    """Verify provider factory selects Demo vs real iGOT based on environment setting."""
    monkeypatch.setattr(settings, "LEARNING_PROVIDER", "demo")
    provider = get_learning_provider()
    assert isinstance(provider, DemoIGOTProvider)

    monkeypatch.setattr(settings, "LEARNING_PROVIDER", "igot")
    provider = get_learning_provider()
    assert isinstance(provider, IGOTProvider)

    # Revert back to demo
    monkeypatch.setattr(settings, "LEARNING_PROVIDER", "demo")


def test_real_igot_provider_unconfigured_error(db):
    """Verify IGOTProvider cleanly rejects calls when credentials are unconfigured."""
    real_provider = IGOTProvider()
    with pytest.raises(NotImplementedError) as exc_info:
        real_provider.search_courses(db)
    assert "Official iGOT Karmayogi API credentials not configured" in str(exc_info.value)

    with pytest.raises(NotImplementedError):
        real_provider.enroll(db, uuid.uuid4(), "IGOT_01")


def test_demo_provider_search_and_competencies(db):
    """Verify DemoIGOTProvider searches and maps courses to official competencies."""
    provider = DemoIGOTProvider()
    courses = provider.search_courses(db, limit=10)
    assert len(courses) > 0

    first = courses[0]
    assert first.provider == "igot"
    assert first.is_demo is True
    assert first.title is not None
    assert len(first.modules) > 0


def test_demo_provider_get_course_details(db, sample_course):
    """Verify get_course returns modules and lessons in correct sequence order."""
    provider = DemoIGOTProvider()
    course = provider.get_course(db, str(sample_course.id))
    assert course is not None
    assert course.id == sample_course.id
    assert len(course.modules) >= 2

    # Check module structure
    mod1 = course.modules[0]
    assert mod1.sequence_order == 1
    assert len(mod1.lessons) >= 1
    assert mod1.lessons[0].content is not None


def test_idempotent_enrollment(db, sample_course):
    """Verify enrollment is idempotent and prevents duplicates."""
    provider = DemoIGOTProvider()
    user = db.query(AppUser).filter(AppUser.email == "employee@mospi.gov.in").first()
    assert user is not None

    # First enrollment
    enroll1 = provider.enroll(db, user_id=user.id, course_id_or_code=str(sample_course.id))
    assert enroll1.status in ["ENROLLED", "IN_PROGRESS", "COMPLETED"]

    # Second enrollment (must return same enrollment ID without duplicate)
    enroll2 = provider.enroll(db, user_id=user.id, course_id_or_code=str(sample_course.id))
    assert enroll2.enrollment_id == enroll1.enrollment_id
    assert "Already enrolled" in enroll2.message or enroll2.status in ["ENROLLED", "IN_PROGRESS", "COMPLETED"]


def test_course_launch(db, sample_course):
    """Verify launch_course returns authorized internal demo player route."""
    provider = DemoIGOTProvider()
    user = db.query(AppUser).filter(AppUser.email == "employee@mospi.gov.in").first()

    launch = provider.launch_course(db, user_id=user.id, course_id_or_code=str(sample_course.id))
    assert launch.provider == "igot"
    assert launch.is_demo is True
    assert launch.launch_url == f"/demo-igot/courses/{sample_course.id}"


def test_module_completion_and_progress_recalculation(db, sample_course):
    """Verify completing a module increments progress percentage accurately."""
    provider = DemoIGOTProvider()
    user = db.query(AppUser).filter(AppUser.email == "employee@mospi.gov.in").first()

    course = provider.get_course(db, str(sample_course.id))
    assert len(course.modules) > 0
    first_mod = course.modules[0]

    # Complete first module
    prog = provider.complete_module(
        db, user_id=user.id, course_id_or_code=str(sample_course.id), module_id_or_code=str(first_mod.id)
    )
    assert prog.progress_percentage > 0.0
    assert prog.completed_modules >= 1

    # Verify first module is marked COMPLETED
    mod_status = next(m for m in prog.modules if m.module_id == first_mod.id)
    assert mod_status.status == "COMPLETED"
    assert mod_status.completed_at is not None


def test_complete_course_and_history(db, sample_course):
    """Verify completing course sets 100% and appears in learning history."""
    provider = DemoIGOTProvider()
    user = db.query(AppUser).filter(AppUser.email == "employee@mospi.gov.in").first()

    completed = provider.complete_course(db, user_id=user.id, course_id_or_code=str(sample_course.id))
    assert completed.status == "COMPLETED"
    assert completed.progress_percentage == 100.0

    history = provider.get_learning_history(db, user_id=user.id)
    assert len(history) > 0
    history_course = next((h for h in history if h.course_id == sample_course.id), None)
    assert history_course is not None
    assert history_course.status == "COMPLETED"


# ==========================================
# REST API ENDPOINT TESTS
# ==========================================

def test_api_list_providers(client, auth_headers):
    resp = client.get("/api/v1/learning/providers", headers=auth_headers)
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 2
    igot = next(p for p in providers if p["code"] == "igot")
    assert igot["name"] == "iGOT Karmayogi"
    assert igot["provider_type"] in ["DEMO", "LIVE"]


def test_api_list_courses(client, auth_headers):
    resp = client.get("/api/v1/learning/courses", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "modules" in data[0]


def test_api_course_flow(client, auth_headers, sample_course):
    """Test full REST endpoint workflow: details -> enroll -> launch -> progress -> complete."""
    course_id = str(sample_course.id)

    # 1. Get Details
    det_resp = client.get(f"/api/v1/learning/courses/{course_id}", headers=auth_headers)
    assert det_resp.status_code == 200
    course_data = det_resp.json()
    assert len(course_data["modules"]) > 0
    first_mod_id = course_data["modules"][0]["id"]

    # 2. Enroll
    enroll_resp = client.post(f"/api/v1/learning/courses/{course_id}/enroll", headers=auth_headers)
    assert enroll_resp.status_code == 200
    assert enroll_resp.json()["course_id"] == course_id

    # 3. Launch
    launch_resp = client.post(f"/api/v1/learning/courses/{course_id}/launch", headers=auth_headers)
    assert launch_resp.status_code == 200
    assert launch_resp.json()["launch_url"] == f"/demo-igot/courses/{course_id}"

    # 4. Progress
    prog_resp = client.get(f"/api/v1/learning/courses/{course_id}/progress", headers=auth_headers)
    assert prog_resp.status_code == 200

    # 5. Complete Module
    mod_resp = client.post(
        f"/api/v1/learning/courses/{course_id}/modules/{first_mod_id}/complete",
        headers=auth_headers,
    )
    assert mod_resp.status_code == 200
    assert mod_resp.json()["completed_modules"] >= 1

    # 6. Complete Entire Course
    comp_resp = client.post(f"/api/v1/learning/courses/{course_id}/complete", headers=auth_headers)
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "COMPLETED"
    assert comp_resp.json()["progress_percentage"] == 100.0

    # 7. History
    hist_resp = client.get("/api/v1/learning/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    hist_items = hist_resp.json()
    assert any(h["course_id"] == course_id for h in hist_items)


def test_unauthorized_access(client, sample_course):
    """Verify learning endpoints enforce authentication."""
    resp = client.get("/api/v1/learning/courses")
    assert resp.status_code == 401

    resp = client.post(f"/api/v1/learning/courses/{sample_course.id}/enroll")
    assert resp.status_code == 401

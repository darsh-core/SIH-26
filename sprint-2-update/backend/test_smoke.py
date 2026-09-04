from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Role, Skill, RoleSkill, Course, UserSkill, AssessmentSession, AssessmentQuestion
from main import app, get_db
import pytest
import time
import requests

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_smoke.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    s_stats = Skill(name="Statistics", category="Core")
    s_python = Skill(name="Python", category="Technical")
    s_sql = Skill(name="SQL", category="Technical")
    s_ml = Skill(name="Machine Learning", category="Advanced")
    s_gis = Skill(name="GIS", category="Domain")
    db.add_all([s_stats, s_python, s_sql, s_ml, s_gis])
    db.commit()
    
    role = Role(name="Statistical Data Analyst")
    db.add(role)
    db.commit()
    
    db.add_all([
        RoleSkill(role_id=role.id, skill_id=s_stats.id, required_level=4, importance=0.9),
        RoleSkill(role_id=role.id, skill_id=s_python.id, required_level=4, importance=0.8),
        RoleSkill(role_id=role.id, skill_id=s_sql.id, required_level=3, importance=0.7),
        RoleSkill(role_id=role.id, skill_id=s_ml.id, required_level=3, importance=0.9),
        RoleSkill(role_id=role.id, skill_id=s_gis.id, required_level=3, importance=0.6),
    ])
    db.commit()
    db.close()

def teardown_module():
    Base.metadata.drop_all(bind=engine)

# ==================================================
# 1. VERIFY REAL OLLAMA INTEGRATION
# ==================================================
def is_ollama_running():
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200 and "llama3.2:latest" in resp.text
    except Exception:
        return False

@pytest.mark.skipif(not is_ollama_running(), reason="Ollama not running or llama3.2:latest missing")
def test_live_ollama_generation():
    response = client.post("/users", json={"name": "Ollama User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    start_time = time.time()
    response = client.get(f"/users/{user_id}/assessment")
    duration = time.time() - start_time
    
    assert response.status_code == 200
    data = response.json()
    assert data["generation_mode"] == "ollama", f"Expected ollama mode, got {data['generation_mode']} (Time: {duration:.2f}s)"
    
    questions = data["questions"]
    assert len(questions) == 10
    
    diff_counts = {"easy": 0, "medium": 0, "hard": 0}
    skill_counts = {}
    
    for q in questions:
        diff_counts[q["difficulty"]] += 1
        skill_counts[q["skill"]] = skill_counts.get(q["skill"], 0) + 1
        assert "correct_answer" not in q
        assert len(q["options"]) == 4
        assert q["question"].strip() != ""
        
    assert diff_counts["easy"] == 3
    assert diff_counts["medium"] == 4
    assert diff_counts["hard"] == 3
    
    # 5 skills, each should have exactly 2 questions based on blueprint logic 10 // 5
    assert len(skill_counts) == 5
    for count in skill_counts.values():
        assert count == 2

    print(f"\n[LIVE OLLAMA TEST] Success. Mode: {data['generation_mode']}. Time: {duration:.2f}s. Qs: {len(questions)}")

# ==================================================
# 3. VERIFY FALLBACK CONTRACT
# ==================================================
def test_fallback_contract():
    import os
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:9999" # Force failure
    
    response = client.post("/users", json={"name": "Fallback User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    response = client.get(f"/users/{user_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    
    assert data["generation_mode"] == "fallback"
    
    questions = data["questions"]
    assert len(questions) == 10
    
    diff_counts = {"easy": 0, "medium": 0, "hard": 0}
    skill_counts = {}
    
    for q in questions:
        diff_counts[q["difficulty"]] += 1
        skill_counts[q["skill"]] = skill_counts.get(q["skill"], 0) + 1
        
    assert diff_counts["easy"] == 3
    assert diff_counts["medium"] == 4
    assert diff_counts["hard"] == 3
    
    assert len(skill_counts) == 5
    for count in skill_counts.values():
        assert count == 2
        
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434" # Restore

# ==================================================
# 4 & 6 & 9. VERIFY SESSION SECURITY, LIFECYCLE, SCORE IMPROVEMENT
# ==================================================
def test_session_security_and_lifecycle():
    # Force fallback for faster testing
    import os
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:9999"
    
    response = client.post("/users", json={"name": "Security User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    response = client.get(f"/users/{user_id}/assessment")
    data = response.json()
    session_id = data["session_id"]
    qs = data["questions"]
    
    # 4a: Session belongs to requested user
    other_user_res = client.post(f"/users/999/assessment/submit", json={"session_id": session_id, "answers": []})
    assert other_user_res.status_code == 404 # User not found
    
    response2 = client.post("/users", json={"name": "Other User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user2_id = response2.json()["id"]
    other_user_res2 = client.post(f"/users/{user2_id}/assessment/submit", json={"session_id": session_id, "answers": []})
    assert other_user_res2.status_code == 403 # Session does not belong to user
    
    # 4b: Invalid answer index rejected
    inv_ans_res = client.post(f"/users/{user_id}/assessment/submit", json={
        "session_id": session_id, 
        "answers": [{"question_id": qs[0]["id"], "selected_option": 5}]
    })
    assert inv_ans_res.status_code == 400
    
    # 4c: Invalid question ID rejected
    inv_q_res = client.post(f"/users/{user_id}/assessment/submit", json={
        "session_id": session_id, 
        "answers": [{"question_id": 99999, "selected_option": 1}]
    })
    assert inv_q_res.status_code == 400
    
    # Test lifecycle logic: generate a NEW session without submitting this one.
    response_new = client.get(f"/users/{user_id}/assessment")
    new_session_id = response_new.json()["session_id"]
    assert session_id != new_session_id
    
    # Submitting older session should fail
    old_submit_res = client.post(f"/users/{user_id}/assessment/submit", json={
        "session_id": session_id,
        "answers": [{"question_id": qs[0]["id"], "selected_option": 1}]
    })
    assert old_submit_res.status_code == 400
    assert "newer assessment is active" in old_submit_res.json()["detail"]
    
    # Submit the new session with BAD answers
    new_qs = response_new.json()["questions"]
    bad_answers = [{"question_id": q["id"], "selected_option": 3} for q in new_qs] # highly likely wrong
    client.post(f"/users/{user_id}/assessment/submit", json={"session_id": new_session_id, "answers": bad_answers})
    
    # Check dashboard - should have low scores
    dash1 = client.get(f"/users/{user_id}/dashboard").json()
    score1 = dash1["overall_competency"]
    
    # Submitting completed session should fail
    re_submit = client.post(f"/users/{user_id}/assessment/submit", json={"session_id": new_session_id, "answers": bad_answers})
    assert re_submit.status_code == 400
    assert "Session is already completed" in re_submit.json()["detail"]
    
    # Retake and get perfect score
    response_perfect = client.get(f"/users/{user_id}/assessment")
    perfect_session_id = response_perfect.json()["session_id"]
    perfect_qs = response_perfect.json()["questions"]
    
    # Get answers directly from db to simulate perfect user
    db = TestingSessionLocal()
    perfect_answers = []
    for q in perfect_qs:
        db_q = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == q["id"]).first()
        perfect_answers.append({"question_id": q["id"], "selected_option": db_q.correct_answer})
    db.close()
    
    client.post(f"/users/{user_id}/assessment/submit", json={"session_id": perfect_session_id, "answers": perfect_answers})
    dash2 = client.get(f"/users/{user_id}/dashboard").json()
    score2 = dash2["overall_competency"]
    
    # Verify score improvement!
    assert score2 > score1
    
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

# ==================================================
# 5. VERIFY ANSWER LEAKAGE
# ==================================================
def test_answer_leakage():
    import os
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:9999"
    
    response = client.post("/users", json={"name": "Leak User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    response = client.get(f"/users/{user_id}/assessment")
    data = response.json()
    
    raw_response_text = response.text.lower()
    
    # Search for forbidden words in the raw API response text
    assert "correct_answer" not in raw_response_text
    assert "correct" not in raw_response_text
    assert "solution" not in raw_response_text
    assert "is_correct" not in raw_response_text

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Role, Skill, RoleSkill, Course, UserSkill, AssessmentSession, AssessmentQuestion
from main import app, get_db, calculate_skill_level
import pytest
from unittest.mock import patch, MagicMock

# Setup in-memory sqlite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

@pytest.fixture(scope="module", autouse=True)
def setup_db():
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
    yield
    Base.metadata.drop_all(bind=engine)

def test_calculate_skill_level():
    assert calculate_skill_level(0, 100) == 1
    assert calculate_skill_level(30, 100) == 2
    assert calculate_skill_level(50, 100) == 3
    assert calculate_skill_level(70, 100) == 4
    assert calculate_skill_level(90, 100) == 5

# Mocking the Ollama Client Response
MOCK_OLLAMA_RESPONSE = """
{
  "questions": [
    {"skill": "Statistics", "difficulty": "easy", "question": "Stats Q1?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "Expl 1"},
    {"skill": "Statistics", "difficulty": "medium", "question": "Stats Q2?", "options": ["A", "B", "C", "D"], "correct_answer": 1, "explanation": "Expl 2"},
    {"skill": "Python", "difficulty": "hard", "question": "Python Q1?", "options": ["A", "B", "C", "D"], "correct_answer": 2, "explanation": "Expl 3"},
    {"skill": "Python", "difficulty": "easy", "question": "Python Q2?", "options": ["A", "B", "C", "D"], "correct_answer": 3, "explanation": "Expl 4"},
    {"skill": "SQL", "difficulty": "medium", "question": "SQL Q1?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "Expl 5"},
    {"skill": "SQL", "difficulty": "hard", "question": "SQL Q2?", "options": ["A", "B", "C", "D"], "correct_answer": 1, "explanation": "Expl 6"},
    {"skill": "Machine Learning", "difficulty": "easy", "question": "ML Q1?", "options": ["A", "B", "C", "D"], "correct_answer": 2, "explanation": "Expl 7"},
    {"skill": "Machine Learning", "difficulty": "medium", "question": "ML Q2?", "options": ["A", "B", "C", "D"], "correct_answer": 3, "explanation": "Expl 8"},
    {"skill": "GIS", "difficulty": "hard", "question": "GIS Q1?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "explanation": "Expl 9"},
    {"skill": "GIS", "difficulty": "medium", "question": "GIS Q2?", "options": ["A", "B", "C", "D"], "correct_answer": 1, "explanation": "Expl 10"}
  ]
}
"""

@patch("ai.assessment_generator.OllamaClient.generate")
def test_user_flow_and_scoring(mock_generate):
    mock_generate.return_value = MOCK_OLLAMA_RESPONSE

    # 1. Create User
    response = client.post("/users", json={"name": "Test User", "department": "DIID", "experience_years": 2, "role_id": 1})
    assert response.status_code == 200
    user_id = response.json()["id"]
    
    # 2. Get Assessment
    response = client.get(f"/users/{user_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    questions = data["questions"]
    
    assert len(questions) == 10
    assert "correct_answer" not in questions[0]
    
    # Extract IDs for answering
    q_stats_e = next(q["id"] for q in questions if q["skill"] == "Statistics" and q["difficulty"] == "easy")
    q_stats_m = next(q["id"] for q in questions if q["skill"] == "Statistics" and q["difficulty"] == "medium")
    
    # 3. Submit Answers
    response = client.post(f"/users/{user_id}/assessment/submit", json={
        "session_id": session_id,
        "answers": [
            {"question_id": q_stats_e, "selected_option": 0}, # Right (1 pt)
            {"question_id": q_stats_m, "selected_option": 0}  # Wrong (0 pt)
        ]
    })
    assert response.status_code == 200
    
    # 4. Dashboard
    response = client.get(f"/users/{user_id}/dashboard")
    assert response.status_code == 200
    dash = response.json()
    
    stats_gap = next(g for g in dash["gaps"] if g["skill"] == "Statistics")
    # 1 out of 3 pts -> 33% -> Level 2
    assert stats_gap["current_level"] == 2
    
@patch("ai.assessment_generator.OllamaClient.generate")
def test_fallback_behavior(mock_generate):
    # Simulate a timeout or failure by returning None
    mock_generate.return_value = None
    
    response = client.post("/users", json={"name": "Fallback User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    response = client.get(f"/users/{user_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    
    # It should fallback to questions.py which has fewer than 10
    assert len(data["questions"]) > 0

@patch("ai.assessment_generator.OllamaClient.generate")
def test_malformed_json_retry(mock_generate):
    # First 2 times return malformed JSON, 3rd time return valid
    mock_generate.side_effect = [
        "not json",
        '{"questions": "wrong type"}',
        MOCK_OLLAMA_RESPONSE
    ]
    
    response = client.post("/users", json={"name": "Retry User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = response.json()["id"]
    
    response = client.get(f"/users/{user_id}/assessment")
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 10
    assert mock_generate.call_count == 3

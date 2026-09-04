from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Role, Document
from main import app, get_db
import pytest
import os
import time

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_docs.db"
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
    role = Role(name="Analyst")
    db.add(role)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_docs.db"):
        os.remove("./test_docs.db")

def test_document_upload_and_extraction():
    # 1. Create a user
    res = client.post("/users", json={"name": "Doc User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = res.json()["id"]

    # 2. Create a dummy txt file
    test_file_path = "test_doc.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test document.\n\nIt has some paragraphs.")

    # 3. Upload file
    with open(test_file_path, "rb") as f:
        response = client.post(
            f"/users/{user_id}/documents",
            files={"file": ("test_doc.txt", f, "text/plain")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "test_doc.txt"
    assert data["file_type"] == ".txt"
    assert data["status"] in ["UPLOADED", "PROCESSING", "READY"]
    
    doc_id = data["id"]
    
    # 4. Wait a tiny bit for background extraction
    time.sleep(0.5)
    
    # 5. Check status
    response = client.get(f"/users/{user_id}/documents/{doc_id}")
    assert response.status_code == 200
    doc_meta = response.json()
    assert doc_meta["status"] == "READY"
    
    # Verify extraction via DB
    db = TestingSessionLocal()
    db_doc = db.query(Document).filter(Document.id == doc_id).first()
    assert db_doc.extracted_text is not None
    assert "This is a test document" in db_doc.extracted_text
    db.close()

    # 6. Test duplicate detection
    with open(test_file_path, "rb") as f:
        response2 = client.post(
            f"/users/{user_id}/documents",
            files={"file": ("test_doc.txt", f, "text/plain")}
        )
    assert response2.status_code == 200
    # Should return the exact same document ID
    assert response2.json()["id"] == doc_id
    
    # 7. Test invalid file type
    with open(test_file_path, "rb") as f:
        bad_res = client.post(
            f"/users/{user_id}/documents",
            files={"file": ("test_doc.exe", f, "application/octet-stream")}
        )
    assert bad_res.status_code == 400
    assert "Unsupported file extension" in bad_res.json()["detail"]
    
    # 8. Test oversize file
    os.environ["MAX_UPLOAD_SIZE"] = "10" # 10 bytes
    large_file_path = "large.txt"
    with open(large_file_path, "w") as f:
        f.write("This is a very large file that exceeds 10 bytes.")
    
    with open(large_file_path, "rb") as f:
        large_res = client.post(
            f"/users/{user_id}/documents",
            files={"file": ("large.txt", f, "text/plain")}
        )
    assert large_res.status_code == 400
    assert "exceeds maximum allowed size" in large_res.json()["detail"]
    os.environ["MAX_UPLOAD_SIZE"] = str(10 * 1024 * 1024)
    os.remove(large_file_path)

    # 9. Test cross user rejection
    res2 = client.post("/users", json={"name": "Hacker", "department": "DIID", "experience_years": 2, "role_id": 1})
    hacker_id = res2.json()["id"]
    
    hack_res = client.get(f"/users/{hacker_id}/documents/{doc_id}")
    assert hack_res.status_code == 404
    
    # Cleanup
    os.remove(test_file_path)

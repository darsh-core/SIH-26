from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Role, Document, DocumentChunk
from main import app, get_db
from services.chunking import DocumentChunker
import pytest
import os
import time
import json

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chunk.db"
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
    if os.path.exists("./test_chunk.db"):
        os.remove("./test_chunk.db")

def test_chunking_logic_direct():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    # Mock normalized document spanning multiple pages
    normalized_doc = {
        "metadata": {"original_filename": "test.pdf"},
        "sections": [
            {
                "index": 1,
                "text": "This is the first paragraph.\n\nThis is the second paragraph which is a bit longer to force a split in the chunker if it exceeds the chunk size.",
                "metadata": {"page": 1}
            },
            {
                "index": 2,
                "text": "This is page two content.",
                "metadata": {"page": 2}
            }
        ]
    }
    
    chunks = chunker.chunk_document(999, normalized_doc)
    
    assert len(chunks) > 0
    assert chunks[0]["document_id"] == 999
    
    # Check that metadata is preserved
    assert "page" in chunks[0]["source_metadata"]
    assert chunks[0]["source_metadata"]["page"] == 1
    assert chunks[0]["source_metadata"]["original_filename"] == "test.pdf"
    
    # Deterministic hash
    assert chunks[0]["chunk_hash"] is not None
    
def test_empty_content_rejected():
    chunker = DocumentChunker()
    empty_doc = {
        "metadata": {"original_filename": "empty.pdf"},
        "sections": [
            {
                "index": 1,
                "text": "   \n  \t  ",
                "metadata": {"page": 1}
            }
        ]
    }
    
    with pytest.raises(ValueError, match="no extractable semantic content"):
        chunker.chunk_document(999, empty_doc)

def test_chunk_overlap():
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=20)
    normalized_doc = {
        "metadata": {"original_filename": "test.txt"},
            "sections": [
                {
                    "index": 1,
                    "text": "A sentence that is quite long. " + "Another sentence that will trigger a split. " + "And a third one.",
                    "metadata": {"section": 1}
                }
            ]  }
    
    chunks = chunker.chunk_document(999, normalized_doc)
    assert len(chunks) > 1
    assert "A sentence that is quite long." in chunks[0]["text"]

def test_api_integration():
    res = client.post("/users", json={"name": "Chunk User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = res.json()["id"]

    test_file_path = "test_chunk_doc.txt"
    with open(test_file_path, "w") as f:
        f.write("Test paragraph one.\n\nTest paragraph two.")

    with open(test_file_path, "rb") as f:
        response = client.post(
            f"/users/{user_id}/documents",
            files={"file": (test_file_path, f, "text/plain")}
        )
    
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    time.sleep(1.0) # Wait for background processing
    
    response = client.get(f"/users/{user_id}/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY_FOR_EMBEDDING"
    assert data["chunk_count"] > 0
    
    # Test reprocessing/duplicate does not double chunks
    with open(test_file_path, "rb") as f:
        res2 = client.post(
            f"/users/{user_id}/documents",
            files={"file": (test_file_path, f, "text/plain")}
        )
    
    assert res2.json()["id"] == doc_id
    
    db = TestingSessionLocal()
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
    assert len(chunks) == data["chunk_count"] # Should not have duplicated
    db.close()
    
    os.remove(test_file_path)

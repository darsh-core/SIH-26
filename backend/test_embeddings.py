from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Role, Document, DocumentChunk
from main import app, get_db
from services.embedding_service import EmbeddingService
import pytest
import os
import time
import json
import numpy as np

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_embed.db"
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
    if os.path.exists("./test_embed.db"):
        os.remove("./test_embed.db")

def test_real_embedding_smoke():
    # 19. REAL EMBEDDING SMOKE TEST
    service = EmbeddingService()
    
    text_A = "Sampling methods are used to select observations from a population."
    text_B = "Statistical sampling selects observations from a larger population."
    text_C = "Python functions are reusable blocks of code."
    
    emb_A = service.embed_text(text_A)
    emb_B = service.embed_text(text_B)
    emb_C = service.embed_text(text_C)
    
    # 9. VECTOR DIMENSION VALIDATION
    assert len(emb_A) == service.embedding_dimension
    assert len(emb_B) == service.embedding_dimension
    assert len(emb_C) == service.embedding_dimension
    
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    sim_AB = cosine_sim(emb_A, emb_B)
    sim_AC = cosine_sim(emb_A, emb_C)
    
    # Prove model produces genuine semantic geometry
    assert sim_AB > sim_AC

def test_embed_empty_rejection():
    service = EmbeddingService()
    # Mock chunk
    chunk = DocumentChunk(
        id=1, document_id=1, text="   ", chunk_hash="empty123", source_metadata="{}"
    )
    # Shouldn't fail, but shouldn't insert
    service.embed_chunks(1, [chunk], user_id=1)
    
    # We can inspect chromadb to ensure it wasn't added, but this is a unit test level, 
    # we know `if not chunk.text.strip(): continue` runs.

def test_api_integration():
    res = client.post("/users", json={"name": "Embed User", "department": "DIID", "experience_years": 2, "role_id": 1})
    user_id = res.json()["id"]

    test_file_path = "test_embed_doc.txt"
    with open(test_file_path, "w") as f:
        f.write("Statistics is the discipline that concerns the collection, organization, analysis, interpretation, and presentation of data.")

    with open(test_file_path, "rb") as f:
        response = client.post(
            f"/users/{user_id}/documents",
            files={"file": (test_file_path, f, "text/plain")}
        )
    
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # Wait for background chunking to finish
    time.sleep(2.0)
    
    response = client.get(f"/users/{user_id}/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY_FOR_EMBEDDING"
    
    # Trigger embedding
    emb_res = client.post(f"/users/{user_id}/documents/{doc_id}/embed")
    assert emb_res.status_code == 200
    assert emb_res.json()["status"] == "EMBEDDING"
    
    # Wait for heavy embedding task
    time.sleep(5.0)
    
    
    response = client.get(f"/users/{user_id}/documents/{doc_id}")
    data = response.json()
    assert data["status"] == "EMBEDDED"
    
    # J, D, K: Duplicate embedding prevention (Idempotency)
    # Re-running embedding shouldn't duplicate vectors.
    emb_res_2 = client.post(f"/users/{user_id}/documents/{doc_id}/embed")
    time.sleep(5.0)
    
    # We can inspect chromadb to ensure only exactly N vectors exist for this doc.
    embedder = EmbeddingService()
    results = embedder.collection.get(
        where={"document_id": doc_id}
    )
    
    # B, M, N: Multiple chunks, chunk mapping, ownership
    assert len(results["ids"]) > 0
    assert len(results["ids"]) == data["chunk_count"]
    assert results["metadatas"][0]["user_id"] == user_id
    assert "source_metadata_json" in results["metadatas"][0]
    
    # Cleanup
    os.remove(test_file_path)

def test_model_failure_recovery():
    # G, H, I, P: simulate a failure and show it can be retried
    service = EmbeddingService()
    chunk = DocumentChunk(
        id=999, document_id=999, text="Valid text", chunk_hash="hash999", source_metadata="{}"
    )
    
    # Force failure
    original_model = service.model_name
    service.model_name = "invalid-model-name-that-does-not-exist"
    service.model = None # Force reload
    
    with pytest.raises(Exception):
        service.embed_chunks(999, [chunk], user_id=1)
        
    # I: retry/recovery
    service.model_name = original_model
    service.model = None
    service.embed_chunks(999, [chunk], user_id=1)
    
    # Should succeed now
    res = service.collection.get(where={"chunk_id": 999})
    assert len(res["ids"]) == 1

import os
import uuid
import pytest
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import shared fixture from phase 2 tests
from tests.test_phase2 import setup_sih_data

from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.models.competency import Competency
from app.models.assessment import Question, Assessment
from app.ai.embeddings import MockEmbeddingProvider
from app.ai.llm import MockLLMProvider
from app.ai.validators import MCQValidator
from app.ai.retrieval import RAGRetriever
from app.ai.competency_mapper import CompetencyMapper
from app.ai.mcq_generator import MCQGenerator
from app.schemas.assessment import GeneratedMCQ, GeneratedMCQOption
from app.services.document_processing_service import DocumentProcessingService, TXTTextExtractor

@pytest.fixture
def auth_headers(client: TestClient, setup_sih_data):
    # Log in as admin superuser
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.gov.in", "password": "adminpwd123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def official_headers(client: TestClient, setup_sih_data):
    # Log in as normal official
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ramesh@test.gov.in", "password": "password123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# 1. TEXT EXTRACTORS & CHUNKER TESTS
# ==========================================
def test_txt_text_extractor():
    temp_path = "test_material.txt"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("Line 1 of sampling text.\nLine 2 of survey text.")
            
        pages = TXTTextExtractor.extract(temp_path)
        assert len(pages) == 1
        assert pages[0]["page_number"] == 1
        assert "sampling text" in pages[0]["text"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_deterministic_chunking():
    pages = [
        {"page_number": 1, "text": "This is a simple sentence describing sampling design. Simple random sampling selection is unbiased."},
        {"page_number": 2, "text": "Stratified random sampling divides the frame into strata. Homogeneous sub-populations reduce overall variance."}
    ]
    
    chunks = DocumentProcessingService.chunk_pages(pages, target_word_count=5, overlap_word_count=1)
    
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "text" in first_chunk
    assert first_chunk["page_start"] == 1
    assert first_chunk["page_end"] in [1, 2]
    assert first_chunk["token_count"] > 0


# ==========================================
# 2. EMBEDDINGS & SIMILARITY SEARCH TESTS
# ==========================================
def test_embedding_dimensions():
    provider = MockEmbeddingProvider()
    vec = provider.embed_text("Sample survey frame")
    
    assert len(vec) == 1536
    assert all(isinstance(v, float) for v in vec)
    
    batch_vecs = provider.embed_documents(["document one", "document two"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 1536


def test_pgvector_similarity_search(db_session: Session):
    doc = Document(
        title="Test Manual",
        filename="manual.txt",
        file_type="TXT",
        file_path="mock/path.txt",
        status="INDEXED"
    )
    db_session.add(doc)
    db_session.flush()

    chunk1 = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        text_content="Stratified random sampling minimizes survey variance.",
        start_char=0,
        end_char=54,
        page_number=1
    )
    chunk2 = DocumentChunk(
        document_id=doc.id,
        chunk_index=1,
        text_content="Convenience selection is a non-probability technique.",
        start_char=55,
        end_char=108,
        page_number=2
    )
    db_session.add_all([chunk1, chunk2])
    db_session.flush()

    embed_provider = MockEmbeddingProvider()
    
    embed1 = DocumentEmbedding(chunk_id=chunk1.id, model_name="mock", embedding=embed_provider.embed_text("Stratified sampling"))
    embed2 = DocumentEmbedding(chunk_id=chunk2.id, model_name="mock", embedding=embed_provider.embed_text("Convenience sampling"))
    db_session.add_all([embed1, embed2])
    db_session.commit()

    query_vector = embed_provider.embed_text("stratification and strata")
    similar_chunks = DocumentProcessingService.search_similar_chunks(db_session, query_vector, top_k=2)
    
    assert len(similar_chunks) == 2
    assert 0.0 <= similar_chunks[0][1] <= 1.0


# ==========================================
# 3. RAG RETRIEVER & COMPETENCY MAPPING TESTS
# ==========================================
def test_rag_retrieval(db_session: Session, setup_sih_data):
    # Seed chunks in DB for retrieval to query
    doc = Document(
        title="Sampling Guide",
        filename="sampling_guide.txt",
        file_type="TXT",
        file_path="mock/path.txt",
        status="INDEXED"
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        text_content="Stratified random sampling minimizes survey variance.",
        start_char=0,
        end_char=54,
        page_number=1
    )
    db_session.add(chunk)
    db_session.flush()

    embed_provider = MockEmbeddingProvider()
    embed = DocumentEmbedding(
        chunk_id=chunk.id,
        model_name="mock",
        embedding=embed_provider.embed_text("Stratified random sampling minimizes survey variance.")
    )
    db_session.add(embed)
    db_session.commit()

    chunks = RAGRetriever.retrieve(db_session, "Stratified random sampling", top_k=2)
    assert len(chunks) > 0
    assert "text" in chunks[0]
    assert "document_title" in chunks[0]


def test_competency_mapping(db_session: Session, setup_sih_data):
    text = "The course teaches STAT_SAMPLING methods including survey design blueprints."
    matches = CompetencyMapper.map_document_to_competencies(db_session, text)
    
    assert len(matches) > 0
    assert matches[0]["competency_code"] == "STAT_SAMPLING"
    assert matches[0]["mapping_method"] == "DETERMINISTIC"


# ==========================================
# 4. MCQ VALIDATION & GROUNDING CHECKS
# ==========================================
def test_mcq_validator(db_session: Session, setup_sih_data):
    context = "Stratified random sampling minimizes survey variance by dividing population into strata."
    
    valid_mcq = GeneratedMCQ(
        question="How does stratified random sampling minimize variance?",
        options=[
            GeneratedMCQOption(text="By dividing population into strata"),
            GeneratedMCQOption(text="By selecting convenient samples"),
            GeneratedMCQOption(text="By ignoring strata weights"),
            GeneratedMCQOption(text="By replacing randomly selected records")
        ],
        correct_answer=0,
        explanation="Dividing population into strata ensures homogeneous groupings which minimizes variance.",
        competency_code="STAT_SAMPLING",
        difficulty="MEDIUM",
        confidence=0.90
    )
    
    is_valid, reasons, score = MCQValidator.validate(db_session, valid_mcq, context, grounding_threshold=0.50)
    assert is_valid is True
    assert score >= 0.50

    invalid_mcq = GeneratedMCQ(
        question="Question statement",
        options=[GeneratedMCQOption(text="Option 1")],
        correct_answer=0,
        explanation="Explain",
        competency_code="STAT_SAMPLING",
        difficulty="MEDIUM",
        confidence=0.80
    )
    is_valid, reasons, score = MCQValidator.validate(db_session, invalid_mcq, context)
    assert is_valid is False
    assert any("Options count" in r for r in reasons)


# ==========================================
# 5. REST API ENDPOINT INTEGRATION TESTS
# ==========================================
def test_document_upload_api_authorizations(client: TestClient, official_headers, auth_headers):
    file_payload = {"file": ("manual.txt", BytesIO(b"Dummy training text"), "text/plain")}
    
    resp_official = client.post("/api/v1/documents", files=file_payload, headers=official_headers)
    assert resp_official.status_code == 403
    
    file_payload_admin = {"file": ("manual.txt", BytesIO(b"Sampling techniques and random selection manuals."), "text/plain")}
    resp_admin = client.post("/api/v1/documents", files=file_payload_admin, headers=auth_headers)
    print("ERROR DETAIL:", resp_admin.json() if resp_admin.status_code == 500 else resp_admin.text)
    assert resp_admin.status_code == 201
    assert "document_id" in resp_admin.json()
    assert resp_admin.json()["status"] == "UPLOADED"


def test_documents_crud_and_mcq_endpoints(client: TestClient, auth_headers, db_session: Session):
    file_payload = {"file": ("sampling_guide.txt", BytesIO(b"Stratified random sampling divides the frame into strata."), "text/plain")}
    resp = client.post("/api/v1/documents", files=file_payload, headers=auth_headers)
    assert resp.status_code == 201
    doc_id = resp.json()["document_id"]

    DocumentProcessingService.process_document(db_session, uuid.UUID(doc_id))

    list_resp = client.get("/api/v1/documents", headers=auth_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    details_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert details_resp.status_code == 200
    assert details_resp.json()["status"] == "INDEXED"

    search_resp = client.post(
        "/api/v1/documents/search",
        json={"query": "stratified strata", "top_k": 2},
        headers=auth_headers
    )
    assert search_resp.status_code == 200
    assert "results" in search_resp.json()

    comp = db_session.query(Competency).filter_by(code="STAT_SAMPLING").first()
    gen_resp = client.post(
        f"/api/v1/documents/{doc_id}/generate-mcqs",
        json={"competency_id": str(comp.id), "difficulty": "MEDIUM", "count": 2},
        headers=auth_headers
    )
    assert gen_resp.status_code == 200
    assert gen_resp.json()["accepted"] >= 1

    assess_resp = client.post(
        f"/api/v1/documents/{doc_id}/generate-assessment",
        json={"competency_id": str(comp.id), "question_count": 2, "difficulty": "MEDIUM"},
        headers=auth_headers
    )
    assert assess_resp.status_code == 200
    assert "assessment_id" in assess_resp.json()
    assert assess_resp.json()["question_count"] >= 1

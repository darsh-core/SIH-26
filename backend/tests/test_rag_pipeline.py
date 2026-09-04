import io
import os
import tempfile
import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.competency import Competency, CompetencyFramework
from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.services.document_processing_service import DocumentProcessingService
from app.ai.retrieval import RAGRetriever
from app.ai.mcq_generator import MCQGenerator
from app.ai.validators import MCQValidator


def test_deterministic_end_to_end_rag_cpi(db_session: Session):
    """
    Deterministic end-to-end RAG test following Section 35:
    1. Ingest document with known CPI facts
    2. Extract & chunk
    3. Embed (384-D)
    4. Store in pgvector
    5. Query 'What does CPI measure?'
    6. Retrieve chunk via similarity
    7. Generate MCQ
    8. Verify source chunk linkage
    9. Verify answer grounded in source
    10. Verify unrelated query yields no hallucination / empty retrieval
    """
    # Configure real embeddings for RAG similarity test
    from app.core.config import settings
    from app.ai import get_embedding_provider
    original_emb = settings.EMBEDDING_PROVIDER
    settings.EMBEDDING_PROVIDER = "sentence_transformer"
    os.environ["EMBEDDING_PROVIDER"] = "sentence_transformer"
    get_embedding_provider(force_refresh=True)

    # 1. Setup Competency
    fw = CompetencyFramework(name="PRICE_STATISTICS_FW", description="Price Statistics Framework")
    db_session.add(fw)
    db_session.commit()

    comp = Competency(
        framework_id=fw.id,
        name="Consumer Price Index Methodology",
        code="STAT_CPI_01",
        description="Compilation, weighting, and release of Consumer Price Indices"
    )
    db_session.add(comp)
    db_session.commit()

    # 2. Ingest document containing known facts
    cpi_text = (
        "India's Consumer Price Index measures changes in the prices paid by consumers for a basket of goods and services. "
        "The CPI is compiled monthly by the National Statistical Office (NSO) under MoSPI. "
        "It covers rural, urban, and combined sectors to measure retail inflation accurately across all Indian states and Union Territories."
    )
    cpi_bytes = cpi_text.encode("utf-8")
    cpi_hash = DocumentProcessingService.compute_sha256(cpi_bytes)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tf.write(cpi_bytes)
        cpi_path = tf.name

    try:
        doc = Document(
            title="MoSPI CPI Technical Note",
            filename="cpi_technical_note.txt",
            file_type="TXT",
            file_path=cpi_path,
            file_size_bytes=len(cpi_bytes),
            checksum=cpi_hash,
            status="UPLOADED"
        )
        db_session.add(doc)
        db_session.commit()

        # Process document (extract, chunk, embed with 384-D, store in pgvector)
        DocumentProcessingService.process_document(db_session, doc.id)

        db_session.refresh(doc)
        assert doc.status in ["READY", "INDEXED"]

        # Verify chunks and pgvector embeddings
        chunks = db_session.query(DocumentChunk).filter_by(document_id=doc.id).all()
        assert len(chunks) >= 1
        chunk_id = chunks[0].id

        embeddings = db_session.query(DocumentEmbedding).filter_by(chunk_id=chunk_id).all()
        assert len(embeddings) >= 1
        assert len(embeddings[0].embedding) == 384

        # 3. Query pgvector similarity for: 'What does CPI measure?'
        retrieved_chunks = RAGRetriever.retrieve(
            db=db_session,
            query="What does CPI measure?",
            document_id=doc.id,
            top_k=2,
            min_similarity=0.1
        )
        assert len(retrieved_chunks) >= 1
        top_chunk = retrieved_chunks[0]
        assert top_chunk["chunk_id"] == chunk_id
        assert "basket of goods and services" in top_chunk["text"]

        # 4. Generate grounded MCQ
        gen_result = MCQGenerator.generate_grounded_mcqs(
            db=db_session,
            document_id=doc.id,
            competency_id=comp.id,
            difficulty="MEDIUM",
            count=1
        )
        assert gen_result["accepted"] >= 1
        mcq = gen_result["questions"][0]

        # 5. Verify source chunk linkage & source traceability
        assert mcq.source_chunk_ids is not None
        assert chunk_id in mcq.source_chunk_ids
        assert mcq.competency_code == "STAT_CPI_01"

        # 6. Verify answer is grounded in source
        is_valid, reasons, grounding_score = MCQValidator.validate(db_session, mcq, top_chunk["text"])
        assert is_valid is True
        assert grounding_score > 0.1

        # 7. Test question unrelated to document
        # Query for quantum entanglement should fail similarity retrieval with min_similarity=0.25
        unrelated_chunks = RAGRetriever.retrieve(
            db=db_session,
            query="superconducting quantum qubit coherence decoherence phase transition entanglement",
            document_id=doc.id,
            top_k=1,
            min_similarity=0.25  # Strict relevance filtering threshold
        )
        assert len(unrelated_chunks) == 0, "Unrelated query should yield 0 chunks above strict relevance threshold"

    finally:
        settings.EMBEDDING_PROVIDER = original_emb
        os.environ["EMBEDDING_PROVIDER"] = original_emb
        get_embedding_provider(force_refresh=True)
        if os.path.exists(cpi_path):
            os.remove(cpi_path)

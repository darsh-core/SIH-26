import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ai import get_embedding_provider
from app.services.document_processing_service import DocumentProcessingService

logger = logging.getLogger("sih-platform.ai.retrieval")

class RAGRetriever:
    """Dedicated RAG retrieval service using PostgreSQL + pgvector (384-D)."""

    @staticmethod
    def retrieve(
        db: Session,
        query: str,
        document_id: Optional[uuid.UUID] = None,
        competency_id: Optional[uuid.UUID] = None,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Receives query text, generates 384-D query embedding, executes pgvector similarity search,
        and returns top-k chunks enriched with source metadata and similarity scores.
        """
        if not query or not query.strip():
            return []

        # 1. Generate query embedding (384 dimensions)
        provider = get_embedding_provider()
        query_vector = provider.embed_text(query)

        # 2. Query similar chunks via pgvector cosine distance
        raw_results = DocumentProcessingService.search_similar_chunks(
            db=db,
            query_embedding=query_vector,
            top_k=top_k * 2,
            document_id=document_id,
            min_similarity=min_similarity
        )

        # 3. Format and enrich with metadata
        ranked_chunks = []
        for chunk, similarity in raw_results:
            doc = chunk.document
            meta = chunk.metadata_json or {}
            
            source_type = meta.get("source_type", "page")
            page_or_slide = chunk.page_number
            
            ranked_chunks.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "document_filename": doc.filename,
                "page": page_or_slide if source_type != "slide" else None,
                "slide": page_or_slide if source_type == "slide" else None,
                "source_type": source_type,
                "text": chunk.text_content,
                "similarity": round(similarity, 4),
                "chunk_index": chunk.chunk_index
            })

        return ranked_chunks[:top_k]

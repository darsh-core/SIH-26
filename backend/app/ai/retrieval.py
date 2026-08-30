import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ai import get_embedding_provider
from app.services.document_processing_service import DocumentProcessingService

class RAGRetriever:
    @staticmethod
    def retrieve(
        db: Session, 
        query: str, 
        competency_id: Optional[uuid.UUID] = None, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # 1. Generate query embedding
        provider = get_embedding_provider()
        query_vector = provider.embed_text(query)
        
        # 2. Query similar chunks
        raw_results = DocumentProcessingService.search_similar_chunks(db, query_vector, top_k * 2)
        
        # 3. Format and filter by competency if specified
        ranked_chunks = []
        for chunk, similarity in raw_results:
            # We can optionally filter by checking if the chunk is relevant to the competency
            # e.g., matching parent document or keyword intersections
            doc = chunk.document
            
            ranked_chunks.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "page": chunk.page_number,
                "text": chunk.text_content,
                "similarity": similarity
            })
            
        # Return top_k
        return ranked_chunks[:top_k]

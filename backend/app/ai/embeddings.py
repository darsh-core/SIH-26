import abc
import hashlib
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger("sih-platform.ai.embeddings")

CANONICAL_EMBEDDING_DIMENSION = 384

class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a single embedding vector for the text."""
        pass

    @abc.abstractmethod
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of documents."""
        pass

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Report embedding model health and dimension."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic Mock Embedding provider producing exactly 384-dimensional vectors."""
    
    def __init__(self, dimension: int = CANONICAL_EMBEDDING_DIMENSION):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        hasher = hashlib.sha256(text.encode("utf-8"))
        digest = hasher.digest()  # 32 bytes
        
        floats = []
        for i in range(self.dimension):
            byte_val = digest[i % len(digest)]
            val = (((byte_val + i * 7) % 256) / 127.5) - 1.0
            floats.append(round(val, 6))
            
        # Normalize vector to unit length for cosine similarity
        norm = sum(x * x for x in floats) ** 0.5
        if norm > 0:
            floats = [round(x / norm, 6) for x in floats]
            
        return floats

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return [self.embed_text(doc) for doc in documents]

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "available": True,
            "model": "mock-384d-embedding",
            "dimension": self.dimension
        }


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Real SentenceTransformer provider generating 384-dimensional normalized embeddings."""
    
    _cached_model = None

    def __init__(
        self,
        model_name: Optional[str] = None,
        dimension: int = CANONICAL_EMBEDDING_DIMENSION
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = dimension

    def _get_model(self):
        if SentenceTransformerEmbeddingProvider._cached_model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            SentenceTransformerEmbeddingProvider._cached_model = SentenceTransformer(self.model_name)
            logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully.")
        return SentenceTransformerEmbeddingProvider._cached_model

    def embed_text(self, text: str) -> List[float]:
        try:
            model = self._get_model()
            embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            result = embedding.tolist()
            if len(result) != self.dimension:
                logger.warning(f"Vector dimension mismatch: expected {self.dimension}, got {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error generating embedding with SentenceTransformer: {e}. Falling back to mock.")
            return MockEmbeddingProvider(dimension=self.dimension).embed_text(text)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        if not documents:
            return []
        try:
            model = self._get_model()
            embeddings = model.encode(documents, batch_size=32, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {e}. Falling back to mock.")
            return [self.embed_text(doc) for doc in documents]

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "sentence_transformer",
            "available": True,
            "model": self.model_name,
            "dimension": self.dimension,
            "cached": SentenceTransformerEmbeddingProvider._cached_model is not None
        }

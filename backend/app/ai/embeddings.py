import abc
import hashlib
from typing import List

class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a single embedding vector for the text."""
        pass

    @abc.abstractmethod
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of documents."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    def embed_text(self, text: str) -> List[float]:
        # Generate exactly 1536 dimensions deterministically based on text content
        hasher = hashlib.sha256(text.encode("utf-8"))
        digest = hasher.digest()  # 32 bytes
        
        # Pad/repeat digest bytes to get exactly 1536 floats normalized to [0, 1]
        floats = []
        for i in range(1536):
            byte_val = digest[i % len(digest)]
            # Add some positional variety
            val = ((byte_val + i) % 256) / 255.0
            floats.append(val)
            
        return floats

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return [self.embed_text(doc) for doc in documents]

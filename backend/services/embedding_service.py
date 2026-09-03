import os
import time
import json
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from models import DocumentChunk

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # Configurable model
        self.model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_dimension = int(os.environ.get("EMBEDDING_DIMENSION", 384))
        
        # We load the model lazily to avoid heavy startup times during tests if not needed
        self.model = None
        
        # Local Vector Store (ChromaDB)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            t0 = time.time()
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded in {time.time() - t0:.2f} seconds")

    def embed_text(self, text: str) -> List[float]:
        self._load_model()
        # The model automatically normalizes if we ask it to, or it produces normalized vectors for all-MiniLM-L6-v2
        # However, sentence_transformers output is a numpy array.
        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_chunks(self, document_id: int, chunks: List[DocumentChunk], user_id: int):
        """
        Embeds a batch of chunks idempotently and stores them in ChromaDB.
        """
        if not chunks:
            return

        self._load_model()

        # Filter out chunks we've already embedded with this exact model
        # The unique ID in ChromaDB will be {chunk_hash}_{model_name}
        # But wait, it's easier to just use `chunk_hash` + `model_name` as the ID in Chroma.
        # If we just upsert with the same ID, it's idempotent.

        texts_to_embed = []
        ids = []
        metadatas = []
        
        for chunk in chunks:
            # We skip empty text defensively
            if not chunk.text or not chunk.text.strip():
                continue
                
            chunk_vector_id = f"{chunk.chunk_hash}_{self.model_name}"
            
            # Preserve ownership and chunk mapping in vector metadata
            # We cannot store nested dicts in chromadb metadata easily, so we stringify source_metadata
            # or flatten it. Stringify is safer.
            meta = {
                "chunk_id": chunk.id,
                "document_id": document_id,
                "user_id": user_id,
                "chunk_hash": chunk.chunk_hash,
                "embedding_model": self.model_name,
                "embedding_dimension": self.embedding_dimension,
                "source_metadata_json": chunk.source_metadata, # JSON string
                "created_at": int(time.time())
            }
            
            texts_to_embed.append(chunk.text)
            ids.append(chunk_vector_id)
            metadatas.append(meta)

        if not texts_to_embed:
            return

        # Batch embed
        t0 = time.time()
        # normalize_embeddings=True guarantees cosine similarity works perfectly using dot product/cosine space in Chroma
        embeddings = self.model.encode(texts_to_embed, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).tolist()
        logger.info(f"Generated {len(texts_to_embed)} embeddings in {time.time() - t0:.2f} seconds")
        
        # Dimension validation
        for i, emb in enumerate(embeddings):
            if len(emb) != self.embedding_dimension:
                raise ValueError(f"Vector dimension mismatch. Expected {self.embedding_dimension}, got {len(emb)}")

        # Upsert to ChromaDB (idempotent by ID)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts_to_embed # Optional, but good for inspection
        )

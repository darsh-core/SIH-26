import os
from typing import Optional
from app.core.config import settings
from .llm import LLMProvider, MockLLMProvider, OllamaLLMProvider, GroqLLMProvider
from .embeddings import EmbeddingProvider, MockEmbeddingProvider, SentenceTransformerEmbeddingProvider, CANONICAL_EMBEDDING_DIMENSION

_cached_llm_provider: Optional[LLMProvider] = None
_cached_embedding_provider: Optional[EmbeddingProvider] = None

def get_llm_provider(force_refresh: bool = False) -> LLMProvider:
    global _cached_llm_provider
    provider_type = os.getenv("AI_PROVIDER", settings.AI_PROVIDER).lower()
    current_type = getattr(_cached_llm_provider, "provider_name", None)
    if _cached_llm_provider is None or force_refresh or current_type != provider_type:
        if provider_type == "groq" or (provider_type != "ollama" and getattr(settings, "GROQ_API_KEY", None)):
            _cached_llm_provider = GroqLLMProvider()
        elif provider_type == "ollama":
            _cached_llm_provider = OllamaLLMProvider()
        else:
            _cached_llm_provider = MockLLMProvider()
    return _cached_llm_provider

def get_embedding_provider(force_refresh: bool = False) -> EmbeddingProvider:
    global _cached_embedding_provider
    provider_type = os.getenv("EMBEDDING_PROVIDER", settings.EMBEDDING_PROVIDER).lower()
    current_type = "sentence_transformer" if isinstance(_cached_embedding_provider, SentenceTransformerEmbeddingProvider) else "mock"
    if _cached_embedding_provider is None or force_refresh or current_type != provider_type:
        if provider_type == "sentence_transformer":
            _cached_embedding_provider = SentenceTransformerEmbeddingProvider()
        else:
            _cached_embedding_provider = MockEmbeddingProvider()
    return _cached_embedding_provider

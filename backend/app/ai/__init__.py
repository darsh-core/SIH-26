import os
from .llm import LLMProvider, MockLLMProvider
from .embeddings import EmbeddingProvider, MockEmbeddingProvider

def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("AI_PROVIDER", "mock").lower()
    if provider_type == "mock":
        return MockLLMProvider()
    return MockLLMProvider()

def get_embedding_provider() -> EmbeddingProvider:
    provider_type = os.getenv("AI_PROVIDER", "mock").lower()
    if provider_type == "mock":
        return MockEmbeddingProvider()
    return MockEmbeddingProvider()

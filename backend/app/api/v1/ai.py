from fastapi import APIRouter
from app.ai import get_llm_provider, get_embedding_provider
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Engine & Health"])

@router.get("/health", summary="AI Engine Health & Availability")
def ai_health():
    """Reports status of LLM provider (Ollama/Mock) and Embedding Provider (SentenceTransformer/Mock)."""
    llm = get_llm_provider()
    embedding = get_embedding_provider()
    
    llm_health = llm.health_check()
    embedding_health = embedding.health_check()
    
    overall = "healthy" if (llm_health.get("available") and embedding_health.get("available")) else "degraded"
    
    return {
        "status": overall,
        "llm": llm_health,
        "embeddings": embedding_health,
        "canonical_dimension": settings.EMBEDDING_DIMENSION
    }

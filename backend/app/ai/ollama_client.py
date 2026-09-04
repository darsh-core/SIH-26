import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger("sih-platform.ai.ollama")

class OllamaClient:
    """Production-ready client for local Ollama inference."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self._client = httpx.Client(timeout=float(self.timeout))

    def is_available(self) -> bool:
        """Checks whether the Ollama server is reachable and running."""
        try:
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def check_model_installed(self) -> bool:
        """Verifies if the configured model tag exists in Ollama."""
        try:
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=3.0)
            if resp.status_code == 200:
                tags = [m.get("name") for m in resp.json().get("models", [])]
                return self.model in tags or any(self.model.split(":")[0] in t for t in tags)
            return False
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        format_json: bool = False,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Calls the Ollama generate endpoint with structured JSON enforcement or free-form text."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_instruction:
            payload["system"] = system_instruction
            
        if schema:
            payload["format"] = schema
        elif format_json:
            payload["format"] = "json"

        try:
            logger.info(f"Dispatching inference request to Ollama ({self.model}) [format_json={format_json or bool(schema)}]")
            resp = self._client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout}s.")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ollama network/connection failure: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Ollama generation: {e}")
            return None

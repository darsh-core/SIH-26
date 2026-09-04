import os
import httpx
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
        self.timeout = int(os.environ.get("OLLAMA_TIMEOUT", "180"))
        self.client = httpx.Client(timeout=self.timeout)

    def generate(self, prompt: str, schema: dict = None) -> str:
        """
        Call Ollama API. 
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": schema if schema else "json"
        }
        
        try:
            response = self.client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.TimeoutException:
            logger.error("Ollama API timeout.")
            return None
        except httpx.RequestError as e:
            logger.error(f"Ollama Request Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ollama unexpected error: {str(e)}")
            return None

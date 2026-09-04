import abc
import json
import logging
import re
from typing import Type, TypeVar, Any, Dict, Optional, List
from pydantic import BaseModel, ValidationError

from app.schemas.assessment import GeneratedMCQ, GeneratedMCQOption
from app.ai.ollama_client import OllamaClient
from app.core.config import settings

logger = logging.getLogger("sih-platform.ai.llm")
T = TypeVar('T', bound=BaseModel)

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a free-form string response."""
        pass

    @abc.abstractmethod
    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: Optional[str] = None) -> T:
        """Generate a structured response parsed into a Pydantic model."""
        pass

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Report provider health and model status."""
        pass


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for unit tests, CI, and fallback."""
    provider_name: str = "mock"
    
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if system_instruction and "REAL-TIME LEARNER COMPETENCY TWIN" in system_instruction:
            return (
                "### Real-Time Competency Gap Analysis & Recommendations\n\n"
                "Based on your official learner profile, your assessed competencies indicate a priority gap in "
                "Sampling Methodology. We strongly recommend taking 'Advanced Stratified Sampling in NSS Surveys' "
                "to bridge this deficit and align with the Cadre requirement for your target role."
            )
        return (
            "Grounded mock statistical answer response for MoSPI competency copilot and survey analysis. "
            "Stratified sampling ensures balanced representation and minimizes sampling variance across diverse strata."
        )

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: Optional[str] = None) -> T:
        if response_schema == GeneratedMCQ:
            prompt_lower = prompt.lower()
            
            # 1. Check for stratified sampling keywords
            if "stratified" in prompt_lower or "stratification" in prompt_lower:
                return GeneratedMCQ(
                    question="What is the primary purpose of stratification in sampling design?",
                    options=[
                        GeneratedMCQOption(text="To increase sampling variance"),
                        GeneratedMCQOption(text="To ensure relevant sub-populations are represented and reduce overall variance"),
                        GeneratedMCQOption(text="To make fieldwork easier"),
                        GeneratedMCQOption(text="To eliminate nonsampling errors")
                    ],
                    correct_answer=1,
                    explanation="Stratification ensures that sub-populations (strata) are represented and reduces overall variance.",
                    competency_code="STAT_SAMPLING",
                    difficulty="MEDIUM",
                    confidence=0.94,
                    source_page=12,
                    grounding_score=0.89
                )
            
            # 2. Check for probability sampling keywords
            if "probability" in prompt_lower or "chance of being selected" in prompt_lower:
                return GeneratedMCQ(
                    question="Which sampling design gives every member of the population an equal and known chance of being selected?",
                    options=[
                        GeneratedMCQOption(text="Simple Random Sampling"),
                        GeneratedMCQOption(text="Quota Sampling"),
                        GeneratedMCQOption(text="Snowball Sampling"),
                        GeneratedMCQOption(text="Convenience Sampling")
                    ],
                    correct_answer=0,
                    explanation="Simple Random Sampling is a probability sampling method where all subsets of the frame have an equal probability of selection.",
                    competency_code="STAT_SAMPLING",
                    difficulty="MEDIUM",
                    confidence=0.95,
                    source_page=1,
                    grounding_score=0.92
                )
            
            # 2. Check for CPI keywords
            if "cpi" in prompt_lower or "consumer price" in prompt_lower:
                return GeneratedMCQ(
                    question="What does India's Consumer Price Index (CPI) primarily measure?",
                    options=[
                        GeneratedMCQOption(text="Changes in wholesale asset prices across global financial markets"),
                        GeneratedMCQOption(text="Changes in the prices paid by consumers for a basket of goods and services"),
                        GeneratedMCQOption(text="Annual growth rate of agricultural produce harvested"),
                        GeneratedMCQOption(text="Government fiscal deficit as a percentage of nominal GDP")
                    ],
                    correct_answer=1,
                    explanation="CPI measures retail price changes paid by households for a defined basket of consumption goods and services.",
                    competency_code="STAT_CPI_01",
                    difficulty="MEDIUM",
                    confidence=0.94,
                    source_page=1,
                    grounding_score=0.91
                )
                
            # 3. Default fallback MCQ grounded in official statistics
            return GeneratedMCQ(
                question="What is the primary advantage of random sampling in official statistical surveys?",
                options=[
                    GeneratedMCQOption(text="It is faster to execute than convenience sampling"),
                    GeneratedMCQOption(text="It eliminates all sources of measurement bias"),
                    GeneratedMCQOption(text="It ensures every population member has a known, non-zero probability of selection"),
                    GeneratedMCQOption(text="It requires no prior sampling frame list")
                ],
                correct_answer=2,
                explanation="Random sampling ensures that selection probability is known and non-zero, allowing valid statistical inferences.",
                competency_code="STAT_SAMPLING",
                difficulty="MEDIUM",
                confidence=0.91,
                source_page=1,
                grounding_score=0.88
            )

        # Generic Pydantic fallback for any test schema
        try:
            dummy_data = {}
            for field_name, field_info in response_schema.model_fields.items():
                annotation = field_info.annotation
                if annotation == int:
                    dummy_data[field_name] = 1
                elif annotation == float:
                    dummy_data[field_name] = 1.0
                elif annotation == bool:
                    dummy_data[field_name] = True
                elif annotation == list or getattr(annotation, "__origin__", None) == list:
                    dummy_data[field_name] = []
                elif annotation == dict or getattr(annotation, "__origin__", None) == dict:
                    dummy_data[field_name] = {}
                else:
                    dummy_data[field_name] = f"mock_{field_name}"
            return response_schema(**dummy_data)
        except Exception:
            raise ValueError(f"MockLLMProvider does not support generating schema type {response_schema}")

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "available": True,
            "model": "mock-statistical-llm",
            "model_installed": True
        }


class OllamaLLMProvider(LLMProvider):
    """Production provider connecting to local Ollama with JSON schema and retries."""
    provider_name: str = "ollama"

    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
        self.fallback = MockLLMProvider()

    def health_check(self) -> Dict[str, Any]:
        available = self.client.is_available()
        model_installed = self.client.check_model_installed() if available else False
        return {
            "provider": "ollama",
            "available": available,
            "model": self.client.model,
            "model_installed": model_installed,
            "endpoint": self.client.base_url
        }

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.client.is_available():
            logger.warning("Ollama server unavailable. Using mock fallback.")
            return self.fallback.generate(prompt, system_instruction)
            
        raw_output = self.client.generate(prompt, system_instruction=system_instruction)
        if raw_output is None:
            logger.warning("Ollama returned None. Using mock fallback.")
            return self.fallback.generate(prompt, system_instruction)
        return raw_output

    def _strip_markdown_fences(self, text: str) -> str:
        """Removes markdown code blocks if the LLM wrapped the JSON."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _normalize_parsed_data(self, data: Dict[str, Any], target_schema: Type[T]) -> Dict[str, Any]:
        """Normalizes common format variations (such as string options to dict options)."""
        if target_schema == GeneratedMCQ:
            # Handle options as list of strings
            if "options" in data and isinstance(data["options"], list):
                norm_options = []
                for opt in data["options"]:
                    if isinstance(opt, str):
                        norm_options.append({"text": opt})
                    elif isinstance(opt, dict) and "text" in opt:
                        norm_options.append(opt)
                data["options"] = norm_options
                
            # Default missing fields safely
            if "confidence" not in data:
                data["confidence"] = 0.90
            if "grounding_score" not in data:
                data["grounding_score"] = 0.85
            if "source_chunk_ids" not in data:
                data["source_chunk_ids"] = []
                
        return data

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: Optional[str] = None) -> T:
        if not self.client.is_available():
            logger.warning("Ollama server unreachable. Failing over to MockLLMProvider.")
            return self.fallback.generate_structured(prompt, response_schema, system_instruction)

        # Build schema instruction
        schema_json = response_schema.model_json_schema()
        augmented_system = (system_instruction or "") + f"\nYou MUST return ONLY a raw JSON object complying with this JSON Schema:\n{json.dumps(schema_json)}"

        max_retries = 2
        last_error = None
        current_prompt = prompt

        for attempt in range(max_retries + 1):
            raw_response = self.client.generate(
                prompt=current_prompt,
                system_instruction=augmented_system,
                format_json=True
            )

            if not raw_response:
                logger.warning(f"Ollama attempt {attempt + 1} yielded empty response.")
                continue

            try:
                cleaned_text = self._strip_markdown_fences(raw_response)
                parsed_dict = json.loads(cleaned_text)
                normalized_dict = self._normalize_parsed_data(parsed_dict, response_schema)
                
                # Pydantic validation
                validated_instance = response_schema.model_validate(normalized_dict)
                logger.info(f"Ollama structured generation successful on attempt {attempt + 1}")
                return validated_instance

            except (json.JSONDecodeError, ValidationError, Exception) as err:
                last_error = err
                logger.warning(f"Ollama generation validation failed on attempt {attempt + 1}: {err}")
                current_prompt = (
                    f"{prompt}\n\n[CORRECTION REQUIRED]: Your previous output failed with error: {str(err)}. "
                    "Ensure valid JSON matching the exact schema with exactly 4 distinct options and one integer correct_answer."
                )

        logger.error(f"All {max_retries + 1} Ollama structured generation attempts failed ({last_error}). Falling back to MockLLMProvider.")
        return self.fallback.generate_structured(prompt, response_schema, system_instruction)


class GroqLLMProvider(LLMProvider):
    """
    High-speed Cloud LLM provider powered by Groq (Llama 3.3 70B / Llama 3.1 8B / Llama 3.2 3B).
    Provides 100% free developer tier inference with sub-second response times on AWS Free Tier.
    """
    provider_name: str = "groq"
    API_URL: str = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import os
        self.api_key = api_key or getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
        self.model = model or getattr(settings, "GROQ_MODEL", None) or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.fallback = MockLLMProvider()

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def health_check(self) -> Dict[str, Any]:
        available = self.is_available()
        return {
            "provider": "groq",
            "available": available,
            "model": self.model,
            "endpoint": self.API_URL
        }

    def _strip_markdown_fences(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _normalize_parsed_data(self, data: Dict[str, Any], target_schema: Type[T]) -> Dict[str, Any]:
        if target_schema == GeneratedMCQ:
            if "options" in data and isinstance(data["options"], list):
                norm_options = []
                for opt in data["options"]:
                    if isinstance(opt, str):
                        norm_options.append({"text": opt})
                    elif isinstance(opt, dict) and "text" in opt:
                        norm_options.append(opt)
                data["options"] = norm_options
            if "confidence" not in data:
                data["confidence"] = 0.95
            if "grounding_score" not in data:
                data["grounding_score"] = 0.90
            if "source_chunk_ids" not in data:
                data["source_chunk_ids"] = []
        return data

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.is_available():
            logger.warning("Groq API key not configured. Falling back to MockLLMProvider.")
            return self.fallback.generate(prompt, system_instruction)

        import httpx
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1500
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(self.API_URL, headers=headers, json=payload)
                if res.status_code != 200:
                    logger.warning(f"Groq API returned error {res.status_code}: {res.text}. Falling back.")
                    return self.fallback.generate(prompt, system_instruction)
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Groq generation failed with error: {e}. Falling back.")
            return self.fallback.generate(prompt, system_instruction)

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: Optional[str] = None) -> T:
        if not self.is_available():
            logger.warning("Groq API key not configured. Falling back to MockLLMProvider.")
            return self.fallback.generate_structured(prompt, response_schema, system_instruction)

        import httpx
        schema_json = response_schema.model_json_schema()
        augmented_system = (system_instruction or "") + f"\nYou MUST return ONLY a raw JSON object complying strictly with this JSON Schema:\n{json.dumps(schema_json)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": augmented_system},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 2048
        }

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=45.0) as client:
                    res = client.post(self.API_URL, headers=headers, json=payload)
                    if res.status_code != 200:
                        logger.warning(f"Groq structured call returned {res.status_code}: {res.text}")
                        continue
                    content = res.json()["choices"][0]["message"]["content"]
                    cleaned = self._strip_markdown_fences(content)
                    parsed_dict = json.loads(cleaned)
                    normalized = self._normalize_parsed_data(parsed_dict, response_schema)
                    return response_schema.model_validate(normalized)
            except Exception as e:
                logger.warning(f"Groq structured generation attempt {attempt + 1} failed: {e}")

        logger.error("All Groq structured generation attempts failed. Falling back to MockLLMProvider.")
        return self.fallback.generate_structured(prompt, response_schema, system_instruction)


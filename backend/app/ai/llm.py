import abc
from typing import Type, TypeVar, Any
from pydantic import BaseModel
from app.schemas.assessment import GeneratedMCQ, GeneratedMCQOption

T = TypeVar('T', bound=BaseModel)

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """Generate a free-form string response."""
        pass

    @abc.abstractmethod
    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: str = None) -> T:
        """Generate a structured response parsed into a Pydantic model."""
        pass


class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str, system_instruction: str = None) -> str:
        return "Grounded mock statistical answer response."

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: str = None) -> T:
        if response_schema == GeneratedMCQ:
            prompt_lower = prompt.lower()
            
            # 1. Check for stratified sampling keywords
            if "stratified" in prompt_lower or "stratification" in prompt_lower:
                mcq = GeneratedMCQ(
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
                return mcq
            
            # 2. Check for probability sampling keywords
            if "probability" in prompt_lower or "chance of being selected" in prompt_lower:
                mcq = GeneratedMCQ(
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
                return mcq
                
            # 3. Default fallback MCQ (always return a valid MCQ grounded in sampling frame logic)
            mcq = GeneratedMCQ(
                question="What is the primary advantage of random sampling in statistical surveys?",
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
            return mcq
            
        raise ValueError(f"MockLLMProvider does not support generating schema type {response_schema}")

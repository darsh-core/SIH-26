import re
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.schemas.assessment import GeneratedMCQ
from app.models.competency import Competency
from app.models.assessment import Question

class MCQValidator:
    @staticmethod
    def validate(
        db: Session, 
        mcq: GeneratedMCQ, 
        context_text: str, 
        grounding_threshold: float = 0.75
    ) -> Tuple[bool, List[str], float]:
        """Validates MCQ structure, duplicate checks, and grounding similarity score."""
        reasons = []
        
        # 1. Non-empty question
        if not mcq.question or not mcq.question.strip():
            reasons.append("Empty question statement")

        # 2. Options count (exactly four options)
        if len(mcq.options) != 4:
            reasons.append(f"Options count is {len(mcq.options)}, expected exactly 4")

        # 3. Correct option check
        if mcq.correct_answer < 0 or mcq.correct_answer >= len(mcq.options):
            reasons.append("Invalid correct_answer index")

        # 4. Non-empty explanation
        if not mcq.explanation or not mcq.explanation.strip():
            reasons.append("Empty answer explanation statement")

        # 5. Competency exists in DB
        comp = db.query(Competency).filter(Competency.code == mcq.competency_code).first()
        if not comp:
            reasons.append(f"Competency code '{mcq.competency_code}' does not exist in framework database")

        # 6. Check for duplicate option text strings
        option_texts = [opt.text.strip().lower() for opt in mcq.options]
        if len(set(option_texts)) != len(option_texts):
            reasons.append("Duplicate option texts detected")

        # 7. Check for duplicate question in DB
        dup_q = db.query(Question).filter(Question.text == mcq.question).first()
        if dup_q:
            reasons.append("Duplicate question statement already exists in database")

        # 8. Grounding / Hallucination Check
        # Compare correct option text + explanation words intersection ratio against source chunk context
        grounding_score = MCQValidator._calculate_grounding_score(mcq, context_text)
        if grounding_score < grounding_threshold:
            reasons.append(f"Grounding score {grounding_score:.2f} is below target threshold of {grounding_threshold}")

        is_valid = len(reasons) == 0
        return is_valid, reasons, grounding_score

    @staticmethod
    def _calculate_grounding_score(mcq: GeneratedMCQ, context_text: str) -> float:
        """Calculates percentage of correct answer words grounded in source text context."""
        context_words = set(re.findall(r"\w+", context_text.lower()))
        if not context_words:
            return 0.0
            
        # Get correct answer text
        correct_text = ""
        if 0 <= mcq.correct_answer < len(mcq.options):
            correct_text = mcq.options[mcq.correct_answer].text
            
        text_to_check = f"{correct_text} {mcq.explanation}".lower()
        check_words = [w for w in re.findall(r"\w+", text_to_check) if len(w) > 3]
        
        if not check_words:
            return 1.0  # safe default if check string is empty
            
        grounded_count = sum(1 for w in check_words if w in context_words)
        return grounded_count / len(check_words)

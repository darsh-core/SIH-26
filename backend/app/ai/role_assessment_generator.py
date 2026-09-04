import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.competency import JobRole, RoleCompetency, Competency
from app.models.assessment import Assessment, Question, QuestionOption, QuestionCompetency
from app.schemas.assessment import GeneratedMCQ, GeneratedMCQOption
from app.ai import get_llm_provider
from app.ai.validators import MCQValidator
from app.core.config import settings

logger = logging.getLogger("sih-platform.ai.role_assessment")

# Fallback question bank for official statistical competencies
OFFICIAL_STATISTICAL_QUESTIONS = {
    "STAT_SAMPLING": [
        {
            "question": "Which probability sampling method divides the population into mutually exclusive subgroups before independent sampling?",
            "options": ["Stratified Random Sampling", "Quota Sampling", "Snowball Sampling", "Convenience Sampling"],
            "correct_answer": 0,
            "explanation": "Stratified random sampling partitions the population into homogeneous strata to reduce sampling variance.",
            "difficulty": "EASY"
        },
        {
            "question": "In multi-stage sampling designs, what distinguishes Primary Sampling Units (PSUs) from Ultimate Sampling Units (USUs)?",
            "options": [
                "PSUs are selected at the first stage, whereas USUs are the final observation units",
                "PSUs are always individual persons, USUs are administrative districts",
                "PSUs have equal variance, USUs have zero variance",
                "PSUs do not require a sampling frame list"
            ],
            "correct_answer": 0,
            "explanation": "Primary Sampling Units (such as census enumeration blocks) are sampled first, followed by successive sampling down to USUs (households).",
            "difficulty": "MEDIUM"
        }
    ],
    "DATA_QUALITY": [
        {
            "question": "What type of survey error occurs when respondents systematically misreport sensitive information during fieldwork?",
            "options": ["Measurement / Response Error", "Sampling Variance", "Coverage Frame Error", "Post-stratification Error"],
            "correct_answer": 0,
            "explanation": "Response error arises from deliberate or accidental misreporting by respondents, representing a form of non-sampling error.",
            "difficulty": "EASY"
        },
        {
            "question": "Which statistical validation metric is most appropriate for assessing internal consistency across related survey items?",
            "options": ["Cronbach's Alpha", "Pearson Chi-Square", "Gini Coefficient", "Durbin-Watson Statistic"],
            "correct_answer": 0,
            "explanation": "Cronbach's alpha evaluates internal consistency and reliability across survey questionnaire items.",
            "difficulty": "HARD"
        }
    ],
    "DEFAULT": [
        {
            "question": "Why are standard metadata registries critical in national statistical systems like MoSPI?",
            "options": [
                "To ensure interoperability, semantic consistency, and comparability of indicators across states",
                "To automatically replace primary field surveys with synthetic estimates",
                "To eliminate all administrative review procedures",
                "To restrict data dissemination to single departments"
            ],
            "correct_answer": 0,
            "explanation": "Standardized metadata classification ensures national and international comparability of statistical indicators.",
            "difficulty": "MEDIUM"
        }
    ]
}


class RoleDiagnosticGenerator:
    """Generates an AI-assisted diagnostic assessment based on a Job Role's required competencies."""

    @staticmethod
    def generate_role_assessment(
        db: Session,
        job_role_id: uuid.UUID,
        total_questions: int = 10
    ) -> Dict[str, Any]:
        role = db.query(JobRole).filter(JobRole.id == job_role_id).first()
        if not role:
            raise ValueError(f"Job Role with ID {job_role_id} not found.")

        role_competencies = db.query(RoleCompetency).filter(
            RoleCompetency.job_role_id == job_role_id
        ).all()

        if not role_competencies:
            raise ValueError(f"Job Role '{role.name}' has no mapped competencies in framework.")

        llm = get_llm_provider()
        if settings.AI_PROVIDER == "groq" or getattr(llm, "provider_name", None) == "groq":
            active_model = getattr(llm, "model", settings.GROQ_MODEL)
        elif settings.AI_PROVIDER == "ollama":
            active_model = settings.OLLAMA_MODEL
        else:
            active_model = "mock-statistical-llm"

        # 1. Blueprint creation
        comp_count = len(role_competencies)
        questions_per_comp = max(1, total_questions // comp_count)
        difficulties = ["EASY", "MEDIUM", "HARD"]

        # 2. Create Assessment Instance
        assessment = Assessment(
            title=f"Diagnostic Competency Checkpoint: {role.name}",
            description=f"AI-generated baseline diagnostic evaluating official competencies required for {role.name}.",
            time_limit_minutes=25,
            pass_percentage=60.0,
            is_ai_generated=True
        )
        db.add(assessment)
        db.flush()

        persisted_questions = []
        q_counter = 0

        for rc in role_competencies:
            comp = rc.competency
            target_for_comp = questions_per_comp
            
            for k in range(target_for_comp):
                if q_counter >= total_questions:
                    break
                    
                diff = difficulties[q_counter % len(difficulties)]
                q_counter += 1

                prompt = (
                    f"You are a senior statistical assessment author for India's Official Statistical System.\n"
                    f"Generate exactly one {diff.lower()}-difficulty Multiple Choice Question evaluating the following competency:\n"
                    f"Role: {role.name}\n"
                    f"Competency Code: {comp.code}\n"
                    f"Competency Title: {comp.name}\n"
                    f"Competency Description: {comp.description or 'Official statistical survey methodology'}\n"
                    f"Required Competency Level: {rc.required_level}/5\n"
                    f"Requirements: 4 options, 1 correct answer (0-indexed), thorough explanation grounded in statistical practice."
                )

                generated_mcq = None
                try:
                    generated_mcq = llm.generate_structured(prompt, GeneratedMCQ)
                    generated_mcq.competency_code = comp.code
                    generated_mcq.difficulty = diff
                    is_valid, _, _ = MCQValidator.validate(db, generated_mcq, comp.description or comp.name)
                    if not is_valid:
                        generated_mcq = None
                except Exception as e:
                    logger.warning(f"Structured role question generation error: {e}")
                    generated_mcq = None

                # Fallback to curated question bank if generation was invalid or failed
                if not generated_mcq:
                    bank = OFFICIAL_STATISTICAL_QUESTIONS.get(comp.code, OFFICIAL_STATISTICAL_QUESTIONS["DEFAULT"])
                    template = bank[k % len(bank)]
                    generated_mcq = GeneratedMCQ(
                        question=template["question"],
                        options=[GeneratedMCQOption(text=t) for t in template["options"]],
                        correct_answer=template["correct_answer"],
                        explanation=template["explanation"],
                        competency_code=comp.code,
                        difficulty=diff,
                        confidence=0.95,
                        grounding_score=0.90
                    )

                # Persist Question entity
                db_q = Question(
                    assessment_id=assessment.id,
                    text=generated_mcq.question,
                    question_type="MCQ",
                    difficulty=generated_mcq.difficulty,
                    explanation=generated_mcq.explanation,
                    confidence=generated_mcq.confidence,
                    generation_method="role-blueprint-v1",
                    ai_model=active_model,
                    grounding_score=generated_mcq.grounding_score,
                    metadata_json={
                        "competency_id": str(comp.id),
                        "competency_name": comp.name,
                        "required_level": rc.required_level,
                        "created_at": datetime.now().isoformat()
                    }
                )
                db.add(db_q)
                db.flush()

                for opt in generated_mcq.options:
                    is_correct = (generated_mcq.options.index(opt) == generated_mcq.correct_answer)
                    db_opt = QuestionOption(
                        question_id=db_q.id,
                        text=opt.text,
                        is_correct=is_correct
                    )
                    db.add(db_opt)

                db_qc = QuestionCompetency(
                    question_id=db_q.id,
                    competency_id=comp.id,
                    target_level=rc.required_level,
                    weight=rc.weight
                )
                db.add(db_qc)
                persisted_questions.append(db_q)

        db.commit()
        db.refresh(assessment)

        return {
            "assessment_id": assessment.id,
            "title": assessment.title,
            "role_name": role.name,
            "job_role": role.name,
            "total_questions": len(persisted_questions),
            "questions": [{"id": q.id, "text": q.text, "difficulty": q.difficulty} for q in persisted_questions],
            "competency_breakdown": [rc.competency.name for rc in role_competencies],
            "competencies_evaluated": [rc.competency.name for rc in role_competencies]
        }

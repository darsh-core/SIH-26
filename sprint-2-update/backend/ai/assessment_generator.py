import json
import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# --- Pydantic Validation Models ---
class GeneratedQuestion(BaseModel):
    skill: str = Field(..., description="The competency skill name")
    difficulty: str = Field(..., description="easy, medium, or hard")
    question: str = Field(..., min_length=5, description="The actual question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    correct_answer: int = Field(..., ge=0, le=3, description="Index of the correct option (0-3)")
    explanation: str = Field(..., min_length=5, description="Explanation for why the answer is correct")

class GeneratedAssessment(BaseModel):
    questions: List[GeneratedQuestion]

class AssessmentGenerator:
    def __init__(self):
        self.ollama = OllamaClient()
        
    def build_blueprint(self, role_name: str, required_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates the structural blueprint for the LLM prompt"""
        
        # Difficulty distribution rule: 3 Easy, 4 Medium, 3 Hard
        # Distribute them across the skills
        skill_count = len(required_skills)
        if skill_count == 0:
            return None
            
        questions_per_skill = max(1, 10 // skill_count)
        
        competencies = []
        for rs in required_skills:
            competencies.append({
                "skill": rs["skill"],
                "required_level": rs["required_level"],
                "question_count": questions_per_skill
            })
            
        return {
            "role": role_name,
            "questions_required": 10,
            "difficulty_distribution": {"easy": 3, "medium": 4, "hard": 3},
            "competencies": competencies
        }
        
    def validate_quality(self, generated: GeneratedAssessment, blueprint: Dict[str, Any]) -> bool:
        """Deterministic quality validation"""
        if len(generated.questions) != 10:
            logger.error(f"Expected 10 questions, got {len(generated.questions)}")
            return False
            
        valid_skills = [c["skill"] for c in blueprint["competencies"]]
        
        seen_questions = set()
        
        diff_counts = {"easy": 0, "medium": 0, "hard": 0}
        
        for q in generated.questions:
            # 1. Skill check
            if q.skill not in valid_skills:
                logger.error(f"Generated invalid skill: {q.skill}")
                return False
                
            # 2. Difficulty check
            if q.difficulty not in diff_counts:
                logger.error(f"Invalid difficulty: {q.difficulty}")
                return False
            diff_counts[q.difficulty] += 1
            
            # 3. Duplicate options check
            if len(set(q.options)) != 4:
                logger.error(f"Duplicate options found in question: {q.question}")
                return False
                
            # 4. Duplicate question check
            norm_q = q.question.lower().strip()
            if norm_q in seen_questions:
                logger.error("Duplicate question generated")
                return False
            seen_questions.add(norm_q)
            
        # 5. Check difficulty distribution (allow minor variations but ensure they exist)
        if diff_counts["easy"] != blueprint["difficulty_distribution"]["easy"]:
            logger.error(f"Expected {blueprint['difficulty_distribution']['easy']} easy, got {diff_counts['easy']}")
            return False
        if diff_counts["medium"] != blueprint["difficulty_distribution"]["medium"]:
            logger.error(f"Expected {blueprint['difficulty_distribution']['medium']} medium, got {diff_counts['medium']}")
            return False
        if diff_counts["hard"] != blueprint["difficulty_distribution"]["hard"]:
            logger.error(f"Expected {blueprint['difficulty_distribution']['hard']} hard, got {diff_counts['hard']}")
            return False
            
        # 6. Check skill coverage
        skill_counts = {c["skill"]: 0 for c in blueprint["competencies"]}
        for q in generated.questions:
            if q.skill in skill_counts:
                skill_counts[q.skill] += 1
                
        for c in blueprint["competencies"]:
            if skill_counts[c["skill"]] != c["question_count"]:
                logger.error(f"Expected {c['question_count']} questions for {c['skill']}, got {skill_counts[c['skill']]}")
                return False
            
        return True

    def generate_assessment(self, user_id: int, role_id: int, role_name: str, required_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Attempts to generate via Ollama. 
        Retries up to 2 times on validation failure.
        Falls back to deterministic question bank on complete failure.
        Returns dict containing questions and generation_mode.
        """
        blueprint = self.build_blueprint(role_name, required_skills)
        if not blueprint:
            return {"mode": "fallback", "questions": []}
            
        system_prompt = f"""You are an expert assessment generator for the role of {role_name}.
You must generate exactly 10 high-quality multiple choice questions.
Questions must test actual understanding, not trivia.
Avoid ambiguous wording.
Avoid multiple correct answers.

Here is the blueprint you must follow EXACTLY:
{json.dumps(blueprint, indent=2)}

You must return a JSON object exactly matching this schema:
{{
  "questions": [
    {{
      "skill": "Skill Name",
      "difficulty": "easy|medium|hard",
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Why option 0 is correct"
    }}
  ]
}}
DO NOT wrap the JSON in markdown blocks. Return ONLY raw JSON.
"""

        # JSON schema for Ollama format parsing
        json_schema = {
          "type": "object",
          "properties": {
            "questions": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "skill": {"type": "string"},
                  "difficulty": {"type": "string"},
                  "question": {"type": "string"},
                  "options": {
                    "type": "array",
                    "items": {"type": "string"}
                  },
                  "correct_answer": {"type": "integer"},
                  "explanation": {"type": "string"}
                },
                "required": ["skill", "difficulty", "question", "options", "correct_answer", "explanation"]
              }
            }
          },
          "required": ["questions"]
        }

        start_time = time.time()
        logger.info(f"assessment_generation_started user_id={user_id} role_id={role_id}")
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            raw_response = self.ollama.generate(system_prompt, schema=json_schema)
            
            if not raw_response:
                continue
                
            try:
                # Strip markdown code blocks if the LLM leaked them despite prompt
                if raw_response.startswith("```json"):
                    raw_response = raw_response[7:-3].strip()
                elif raw_response.startswith("```"):
                    raw_response = raw_response[3:-3].strip()
                    
                parsed_json = json.loads(raw_response)
                validated_model = GeneratedAssessment(**parsed_json)
                
                if self.validate_quality(validated_model, blueprint):
                    duration = time.time() - start_time
                    logger.info(f"assessment_generation_success user_id={user_id} duration={duration:.2f}s fallback=false")
                    
                    # Convert to dictionaries for the rest of the application
                    return {"mode": "ollama", "questions": [q.model_dump() for q in validated_model.questions]}
                    
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Generation validation failed on attempt {attempt+1}: {str(e)}")
                continue

        # Fallback
        duration = time.time() - start_time
        logger.error(f"assessment_generation_failed user_id={user_id} duration={duration:.2f}s")
        logger.info(f"assessment_generation_fallback user_id={user_id} role_id={role_id}")
        
        from questions import get_assessment_for_blueprint
        fallback_qs = get_assessment_for_blueprint(blueprint)
        return {"mode": "fallback", "questions": fallback_qs}

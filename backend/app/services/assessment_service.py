import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.assessment import Assessment, Question, QuestionOption, AssessmentAttempt, AttemptAnswer, QuestionCompetency
from app.models.competency import UserCompetency, CompetencyEvidence, Competency
from app.schemas.assessment import AssessmentSubmitRequest, AssessmentResultResponse, AssessmentAttemptResponse, CompetencyPerformance
from app.schemas.competency import CompetencyUpdateRequest

class AssessmentService:
    
    @staticmethod
    def get_assessments(db: Session, skip: int = 0, limit: int = 10) -> Tuple[List[Assessment], int]:
        query = db.query(Assessment)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_assessment(db: Session, assessment_id: uuid.UUID) -> Optional[Assessment]:
        return db.query(Assessment).filter(Assessment.id == assessment_id).first()

    @staticmethod
    def start_attempt(db: Session, assessment_id: uuid.UUID, user_id: uuid.UUID) -> AssessmentAttempt:
        assessment = AssessmentService.get_assessment(db, assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
            
        attempt = AssessmentAttempt(
            assessment_id=assessment_id,
            user_id=user_id,
            score=0.0,
            is_passed=False,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc) # default, will overwrite on submit
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def submit_attempt(
        db: Session,
        attempt_id: uuid.UUID,
        user_id: uuid.UUID,
        submission: AssessmentSubmitRequest
    ) -> AssessmentResultResponse:
        # Load attempt
        attempt = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.id == attempt_id,
            AssessmentAttempt.user_id == user_id
        ).first()
        
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment attempt not found"
            )
            
        # Ensure not already completed
        if attempt.metadata_json and attempt.metadata_json.get("submitted", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This assessment attempt has already been submitted"
            )

        assessment = attempt.assessment
        
        # Load questions to validate options
        questions = db.query(Question).filter(Question.assessment_id == assessment.id).all()
        question_map = {q.id: q for q in questions}
        
        # Track answers correctness and group by competency
        correct_count = 0
        total_questions = len(questions)
        
        if total_questions == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment has no questions"
            )

        # Store submitted answers
        submitted_dict = {ans.question_id: ans.selected_option_id for ans in submission.answers}
        
        # Map for competency performance evaluation
        # competency_id -> { "correct": int, "total": int, "target_level": int, "competency": Competency }
        comp_perf: Dict[uuid.UUID, Dict[str, Any]] = {}

        # Validate and score each question
        for q in questions:
            selected_option_id = submitted_dict.get(q.id)
            if not selected_option_id:
                # Unanswered or skipped, treated as incorrect
                continue
                
            # Fetch option
            option = db.query(QuestionOption).filter(
                QuestionOption.id == selected_option_id,
                QuestionOption.question_id == q.id
            ).first()
            
            if not option:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Selected option {selected_option_id} does not belong to question {q.id}"
                )
                
            is_correct = option.is_correct
            if is_correct:
                correct_count += 1
                
            # Create attempt answer record
            attempt_answer = AttemptAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option_id=selected_option_id,
                is_correct=is_correct
            )
            db.add(attempt_answer)

            # Extract question competencies
            q_comps = db.query(QuestionCompetency).filter(
                QuestionCompetency.question_id == q.id
            ).all()
            
            for qc in q_comps:
                comp_id = qc.competency_id
                if comp_id not in comp_perf:
                    comp_perf[comp_id] = {
                        "correct": 0,
                        "total": 0,
                        "target_level": qc.target_level,
                        "competency": qc.competency
                    }
                comp_perf[comp_id]["total"] += 1
                if is_correct:
                    comp_perf[comp_id]["correct"] += 1

        # Calculate score
        final_score = (correct_count / total_questions) * 100.0
        is_passed = final_score >= assessment.pass_percentage
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - attempt.started_at).seconds

        # Update attempt
        attempt.score = round(final_score, 1)
        attempt.is_passed = is_passed
        attempt.completed_at = completed_at
        attempt.duration_seconds = duration
        attempt.metadata_json = {"submitted": True}
        db.flush()

        # Update user competency based on performance feedback loop
        performances: List[CompetencyPerformance] = []
        
        for comp_id, perf in comp_perf.items():
            competency = perf["competency"]
            perf_score = (perf["correct"] / perf["total"]) * 100.0
            
            # Map accuracy to level gain: target_level * (correct / total)
            level_gain = float(perf["target_level"]) * (perf["correct"] / perf["total"])
            
            # Fetch current competency level
            user_comp = db.query(UserCompetency).filter(
                UserCompetency.user_id == user_id,
                UserCompetency.competency_id == comp_id
            ).first()
            
            old_level = user_comp.current_level if user_comp else 0.0
            new_level = max(old_level, round(level_gain, 1))

            # Trigger update if level increased
            if not user_comp or new_level > old_level:
                # Find or create
                if not user_comp:
                    user_comp = UserCompetency(
                        user_id=user_id,
                        competency_id=comp_id,
                        current_level=new_level,
                        last_evaluated_at=datetime.now(timezone.utc),
                        status="EVALUATED"
                    )
                    db.add(user_comp)
                    db.flush()
                else:
                    user_comp.current_level = new_level
                    user_comp.last_evaluated_at = datetime.now(timezone.utc)
                
                # Write to evidence
                evidence = CompetencyEvidence(
                    user_competency_id=user_comp.id,
                    type="ASSESSMENT",
                    source_id=attempt.id,
                    description=f"Assessed via '{assessment.title}' scoring {perf_score:.1f}% accuracy on targeted Level {perf['target_level']} questions.",
                    verified_by=None,
                    verified_at=None,
                    metadata_json={
                        "old_level": old_level,
                        "new_level": new_level,
                        "accuracy": perf_score,
                        "target_level": perf["target_level"]
                    }
                )
                db.add(evidence)

            performances.append(
                CompetencyPerformance(
                    competency_code=competency.code,
                    competency_name=competency.name,
                    score=round(perf_score, 1),
                    questions_answered=perf["total"],
                    questions_correct=perf["correct"]
                )
            )

        db.commit()
        db.refresh(attempt)
        
        attempt_res = AssessmentAttemptResponse.model_validate(attempt)
        
        return AssessmentResultResponse(
            attempt=attempt_res,
            score=attempt.score,
            is_passed=attempt.is_passed,
            competency_performances=performances
        )

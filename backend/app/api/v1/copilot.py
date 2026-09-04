import logging
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_authenticated_user
from app.models.user import AppUser
from app.models.course import Course, TrainingProgram
from app.services.gap_engine import GapEngine
from app.services.recommendation_service import RecommendationService
from app.ai import get_llm_provider
from app.ai.retrieval import RAGRetriever
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotCitation,
    QuickPrompt
)

logger = logging.getLogger("sih-platform.copilot")

router = APIRouter(prefix="/copilot", tags=["MoSPI Statistical AI Copilot"])

DEFAULT_QUICK_PROMPTS = [
    QuickPrompt(
        title="Analyze My Skill Gaps",
        prompt="Analyze my current competency gaps and overall role readiness based on my latest assessment.",
        category="Competency Twin",
        icon="Brain"
    ),
    QuickPrompt(
        title="Recommended Learning & Why",
        prompt="What courses do you recommend for my role, and why specifically do you suggest each one?",
        category="Explainable Pathways",
        icon="Target"
    ),
    QuickPrompt(
        title="Crop Estimation (GCES vs TRS)",
        prompt="Explain the difference between Timely Reporting Scheme (TRS) and General Crop Estimation Surveys (GCES) in agricultural statistics.",
        category="Agricultural Statistics",
        icon="Wheat"
    ),
    QuickPrompt(
        title="CPI Basket & Weighting",
        prompt="How is the Consumer Price Index (CPI) basket and weighting diagram constructed according to MoSPI methodology?",
        category="Price Indices",
        icon="TrendingUp"
    ),
    QuickPrompt(
        title="Stratified Random Sampling",
        prompt="Explain how Stratified Random Sampling minimizes sampling variance and why it is used in NSS household surveys.",
        category="Sampling Theory",
        icon="Layers"
    ),
    QuickPrompt(
        title="Quick Statistical Drill",
        prompt="Give me a 3-question rapid quiz on sampling theory and estimation with explanations.",
        category="Interactive Quiz",
        icon="HelpCircle"
    )
]

@router.get("/quick-prompts", response_model=List[QuickPrompt], summary="Curated MoSPI statistical prompts")
def get_quick_prompts():
    """Returns curated prompts to jumpstart official learning conversations."""
    return DEFAULT_QUICK_PROMPTS

@router.post("/chat", response_model=CopilotChatResponse, summary="Chat with MoSPI Statistical AI Copilot")
def chat_with_copilot(
    req: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[AppUser] = Depends(get_optional_authenticated_user)
):
    """
    100% on-premise, real-time conversational AI copilot.
    - Dynamically ingests the learner's actual profile, competency gaps, and recommendations.
    - Retrieves relevant MoSPI knowledge chunks via pgvector (384-D).
    - Generates grounded, explainable pedagogical responses in real time using local Ollama (Llama 3.2).
    """
    try:
        # 1. Resolve Target User Context (for skill gap analysis & personalized explainability)
        target_user = current_user
        if not target_user and req.user_id:
            target_user = db.query(AppUser).filter(AppUser.id == req.user_id).first()

        user_context_block = ""
        if target_user:
            try:
                prof = target_user.profile
                name = f"{prof.first_name or ''} {prof.last_name or ''}".strip() if prof else "Statistical Officer"
                department = prof.department if prof and prof.department else "Statistical Wing"
                designation = prof.designation if prof and prof.designation else "Statistical Officer"
                
                # Fetch live gaps
                gap_data = GapEngine.calculate_gaps(db, user_id=target_user.id)
                role_name = getattr(gap_data.role, "title", getattr(gap_data.role, "name", designation)) if gap_data and gap_data.role else designation
                readiness = gap_data.overall_readiness if gap_data else 0.0

                gaps_lines = []
                for g in (gap_data.gaps if gap_data else []):
                    gaps_lines.append(
                        f"- {g.competency_name} ({g.competency_code}): Current Level {g.current_level:.1f}/5.0 | "
                        f"Target Required Level {g.required_level:.1f}/5.0 | Deficit: {g.gap:.1f} levels | Priority: {g.priority}"
                    )

                # Fetch recommendations
                recs = RecommendationService.get_recommendations(db, user_id=target_user.id)
                recs_lines = []
                for r in recs[:5]:
                    title = r.course.title if r.item_type == "COURSE" and r.course else (r.training_program.title if r.training_program else "Training Module")
                    provider = r.course.provider if r.item_type == "COURSE" and r.course else "NSSTA Academy"
                    dur = f"{r.course.duration_minutes} mins" if r.item_type == "COURSE" and r.course else "Multiday"
                    recs_lines.append(
                        f"- '{title}' [{provider} | {dur}]: Aligned to bridge {r.competency.name} ({r.competency.code}) deficit with {r.recommendation_score:.1f}% fit.\n"
                        f"  Explanation/Rationale: {r.logic_explanation}"
                    )

                user_context_block = (
                    "\n--- REAL-TIME LEARNER COMPETENCY TWIN & PROFILE ---\n"
                    f"Learner Name: {name}\n"
                    f"Job Cadre / Designation: {designation}\n"
                    f"Target Cadre Role: {role_name}\n"
                    f"Department: {department}\n"
                    f"Overall Cadre Readiness: {readiness:.1f}%\n\n"
                    f"EVALUATED COMPETENCY DEFICITS & GAPS:\n"
                    f"{chr(10).join(gaps_lines) if gaps_lines else 'No critical competency deficits. Cadre requirements met.'}\n\n"
                    f"PERSONALIZED RECOMMENDED TRAINING (iGOT Karmayogi & NSSTA):\n"
                    f"{chr(10).join(recs_lines) if recs_lines else 'No pending recommendations.'}\n"
                    "---------------------------------------------------\n"
                )
            except Exception as ctx_err:
                logger.warning(f"Could not construct full learner context: {ctx_err}")

        # 2. RAG Retrieval from PostgreSQL pgvector (if topic matches official documents)
        ranked_chunks = []
        try:
            ranked_chunks = RAGRetriever.retrieve(
                db=db,
                query=req.message,
                document_id=req.document_id,
                competency_id=req.competency_id,
                top_k=4,
                min_similarity=0.25
            )
        except Exception as rag_err:
            logger.warning(f"RAG retrieval encountered warning: {rag_err}")

        # 3. Prepare Citations
        citations: List[CopilotCitation] = []
        for c in ranked_chunks:
            snippet = c.get("text", "")
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."
            citations.append(CopilotCitation(
                document_id=c["document_id"],
                document_title=c["document_title"],
                document_filename=c["document_filename"],
                page=c.get("page"),
                slide=c.get("slide"),
                source_type=c.get("source_type", "page"),
                text_snippet=snippet,
                similarity=c.get("similarity", 0.0)
            ))

        # 4. Formulate Pedagogical System Prompt
        system_instruction = (
            "You are Vivi, the official MoSPI Statistical AI Copilot and 24/7 Learning Mentor for the Indian Official Statistical System (Ministry of Statistics and Programme Implementation - MoSPI, NSSO, CSO, NSSTA).\n\n"
            "Your Responsibilities:\n"
            "1. Real-Time Questions: Answer statistical theory, sampling, survey design, index formula, and fieldwork guideline questions thoroughly and clearly in real time.\n"
            "2. Skill Gap Analysis: When asked to analyze the learner's skill gaps or readiness, review the learner's live profile below, explicitly state their current vs required competency levels, highlight high-priority deficits, and provide encouraging feedback.\n"
            "3. Recommendation & Explainability: When asked what courses to take or WHY a course is recommended, explain the specific pedagogical and operational rationale: connect their current competency deficit to the course curriculum and explain how bridging this gap helps them perform their official duties (e.g. conducting valid sample surveys, computing CPI weights without bias, minimizing sampling variance).\n\n"
            "Formatting & Tone Guidelines:\n"
            "- Answer directly in clean GitHub-flavored markdown with bold keywords, clean bulleted lists, and structured sections.\n"
            "- Do NOT wrap your entire answer in JSON. Output natural, human-readable markdown text.\n"
            "- Maintain an authoritative, knowledgeable, yet deeply supportive mentor tone.\n"
        )

        if user_context_block:
            system_instruction += user_context_block

        if ranked_chunks:
            context_blocks = []
            for idx, c in enumerate(ranked_chunks):
                loc = f"Page {c['page']}" if c.get("page") else (f"Slide {c['slide']}" if c.get("slide") else "Section")
                context_blocks.append(f"--- Reference [{idx+1}]: {c['document_title']} ({loc}) ---\n{c['text']}")
            context_str = "\n\n".join(context_blocks)
            system_instruction += (
                "\nOFFICIAL MOSPI MANUAL EXCERPTS (Use these to ground your answer):\n"
                f"{context_str}\n\n"
                "Grounding Rules:\n"
                "- Directly cite and reference the excerpts above when explaining methodologies or official figures.\n"
            )

        # 5. Assemble Multi-turn History
        prompt_parts = []
        if req.history:
            recent_turns = req.history[-6:]  # Keep last 3 exchanges
            for turn in recent_turns:
                role_label = "Learner" if turn.role == "user" else "Vivi (Statistical Mentor)"
                prompt_parts.append(f"{role_label}: {turn.content}")
        
        prompt_parts.append(f"Learner: {req.message}")
        prompt_parts.append("Vivi (Statistical Mentor):")
        full_prompt = "\n\n".join(prompt_parts)

        # 6. Call LLM (Groq / Ollama / Fallback)
        llm = get_llm_provider()
        model_str = getattr(llm, "model", None) or getattr(getattr(llm, "client", None), "model", "llama3.2:3b")

        reply_text = llm.generate(
            prompt=full_prompt,
            system_instruction=system_instruction
        )

        # Clean JSON wrappers if emitted by Llama
        if reply_text and ("{" in reply_text and "}" in reply_text):
            try:
                clean_json = reply_text.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()
                
                parsed = json.loads(clean_json)
                if isinstance(parsed, dict):
                    if "content" in parsed:
                        reply_text = parsed["content"]
                        if "title" in parsed and parsed["title"]:
                            reply_text = f"### {parsed['title']}\n\n{reply_text}"
                    elif "reply" in parsed:
                        reply_text = parsed["reply"]
                    elif "message" in parsed:
                        reply_text = parsed["message"]
                    elif "explanation" in parsed:
                        reply_text = parsed["explanation"]
            except Exception:
                pass  # Fall back to raw text if not valid JSON

        if not reply_text or not reply_text.strip():
            reply_text = (
                "Hello! As your MoSPI Statistical Copilot, I am here to assist you with survey designs, "
                "sampling methodologies, competency gap analysis, and course recommendations. "
                "Please feel free to ask any specific question about your skill profile or training modules!"
            )

        return CopilotChatResponse(
            reply=reply_text,
            citations=citations,
            model=model_str,
            grounded=len(citations) > 0,
            session_id=req.session_id or "default_session"
        )

    except Exception as e:
        logger.error(f"Copilot chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot inference encountered an error: {str(e)}"
        )

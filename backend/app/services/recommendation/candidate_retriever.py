from typing import List, Optional
from pydantic import BaseModel

from sqlalchemy.orm import Session
from app.integrations.learning_provider import get_learning_provider
from app.integrations.provider import MockIGOTProvider, MockNSSTAProvider

class CandidateMapping(BaseModel):
    competency_code: str
    target_level: int
    weight: float

class RecommendationCandidate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    provider: str  # "iGOT" or "NSSTA"
    difficulty: str  # "Beginner", "Intermediate", "Advanced"
    language: str
    url: Optional[str] = None
    duration_minutes: int  # Normalized to minutes (NSSTA: days * 8 * 60)
    mode: str  # "ONLINE", "OFFLINE", "HYBRID"
    eligibility_criteria: Optional[str] = None
    tpac_recommendation: Optional[str] = None
    competency_mappings: List[CandidateMapping]


class CandidateRetriever:
    
    @staticmethod
    def retrieve_candidates(comp_codes: List[str], db: Optional[Session] = None) -> List[RecommendationCandidate]:
        """
        Queries abstract provider interfaces and returns a normalized candidate list
        addressing any of the target competency codes.
        """
        candidates = []
        
        # 1. Retrieve from iGOT Learning Provider
        if db is not None:
            try:
                learning_provider = get_learning_provider()
                courses = learning_provider.search_courses(db, competency_codes=comp_codes)
                for c in courses:
                    candidates.append(
                        RecommendationCandidate(
                            code=c.external_course_id,
                            title=c.title,
                            description=c.description,
                            provider="iGOT",
                            difficulty=c.difficulty,
                            language=c.language or "English",
                            url=c.course_url,
                            duration_minutes=c.duration_minutes,
                            mode="ONLINE",
                            competency_mappings=[
                                CandidateMapping(
                                    competency_code=m.code,
                                    target_level=m.target_level,
                                    weight=m.weight
                                ) for m in c.competencies
                            ]
                        )
                    )
            except Exception as e:
                print(f"Error querying learning provider: {e}")
                
        # Fallback to MockIGOTProvider if no db candidates retrieved
        if not candidates:
            igot_provider = MockIGOTProvider()
            try:
                igot_courses = igot_provider.get_courses()
                for c in igot_courses:
                    matches = [m for m in c.competency_mappings if m.competency_code in comp_codes]
                    if not matches:
                        continue
                    diff = c.difficulty.capitalize() if c.difficulty else "Beginner"
                    candidates.append(
                        RecommendationCandidate(
                            code=c.code,
                            title=c.title,
                            description=c.description,
                            provider="iGOT",
                            difficulty=diff,
                            language=c.language or "English",
                            url=c.url,
                            duration_minutes=c.duration_minutes,
                            mode="ONLINE",
                            competency_mappings=[
                                CandidateMapping(
                                    competency_code=m.competency_code,
                                    target_level=m.target_level,
                                    weight=m.weight
                                ) for m in c.competency_mappings
                            ]
                        )
                    )
            except Exception as e:
                print(f"Error retrieving from mock iGOT provider: {e}")
            
        # 2. Retrieve from NSSTA
        nssta_provider = MockNSSTAProvider()
        try:
            nssta_programs = nssta_provider.get_training_programs()
            for p in nssta_programs:
                matches = [m for m in p.competency_mappings if m.competency_code in comp_codes]
                if not matches:
                    continue
                
                # Map days to duration_minutes: 1 day = 8 hours = 480 minutes
                duration_minutes = (p.duration_days or 1) * 8 * 60
                
                # Determine difficulty dynamically or map to Intermediate/Advanced
                # Since NSSTA programs are professional academy courses, we treat them as Intermediate/Advanced
                # If survey methodology estimation is in title -> Advanced, else Intermediate
                diff = "Advanced" if "advanced" in p.title.lower() or "executive" in p.title.lower() else "Intermediate"
                
                candidates.append(
                    RecommendationCandidate(
                        code=p.code,
                        title=p.title,
                        description=p.description,
                        provider="NSSTA",
                        difficulty=diff,
                        language="English",
                        url=f"https://nssta.gov.in/programs/{p.code}",
                        duration_minutes=duration_minutes,
                        mode=p.mode or "OFFLINE",
                        eligibility_criteria=p.eligibility_criteria,
                        tpac_recommendation=p.tpac_recommendation,
                        competency_mappings=[
                            CandidateMapping(
                                competency_code=m.competency_code,
                                target_level=m.target_level,
                                weight=m.weight
                            ) for m in p.competency_mappings
                        ]
                    )
                )
        except Exception as e:
            print(f"Error retrieving from NSSTA provider: {e}")
            
        return candidates

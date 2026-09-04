import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models.user import AppUser, UserProfile
from app.models.competency import UserCompetency

router = APIRouter(tags=["Profiles"])

@router.get("/profile/me", summary="Get Current User AI Competency Twin Profile")
@router.get("/profiles/me", summary="Get Current User AI Competency Twin Profile (Alias)")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_authenticated_user)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "designation": profile.designation,
        "department": profile.department,
        "contact_number": profile.contact_number,
        "gender": profile.gender,
        "date_of_joining": profile.date_of_joining.isoformat() if profile.date_of_joining else None,
        "bio": profile.bio,
        "job_role": {
            "id": str(profile.job_role.id),
            "name": profile.job_role.name,
            "code": profile.job_role.code,
        } if profile.job_role else None,
        "competencies": [
            {
                "competency_id": str(c.competency_id),
                "competency_code": c.competency.code if c.competency else "",
                "competency_name": c.competency.name if c.competency else "",
                "current_level": c.current_level,
                "status": c.status
            }
            for c in user_comps
        ]
    }

@router.get("/profiles", summary="Profile Alias Check")
def get_profile_alias():
    return {"message": "Profiles are managed directly under the /users/{user_id}/profile endpoint."}

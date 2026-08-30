from fastapi import APIRouter

router = APIRouter(prefix="/profiles", tags=["Profiles (Legacy/Alias)"])

@router.get("", summary="Profile Alias Check")
def get_profile_alias():
    return {"message": "Profiles are managed directly under the /users/{user_id}/profile endpoint."}

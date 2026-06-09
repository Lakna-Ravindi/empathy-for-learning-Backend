# app/routes/profile_routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.profile_models import ProfileUpdate, ProfileResponse
from app.services.profile_service import update_user_profile, delete_user_profile, get_user_profile
from app.core.validators import ValidationError
from app.dependencies.auth_dependency import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile
    
    Returns authenticated user's profile information.
    Requires authentication.
    """
    try:
        user_profile = await get_user_profile(str(current_user["_id"]))
        return ProfileResponse(
            ageGroup=user_profile.get("ageGroup")
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/me", response_model=dict)
async def update_current_user_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile
    
    Requires authentication.
    
    Validation Rules:
    - ageGroup: must be valid enum (Below 16 years, 16–18 years, 19–21 years, 22-25 years, 26+ years)
    """
    try:
        updated_user = await update_user_profile(str(current_user["_id"]), profile_data)
        return {
            "message": "Profile updated successfully",
            "user": {
                "fullName": updated_user.get("fullName"),
                "email": updated_user.get("email"),
                "ageGroup": updated_user.get("ageGroup")
            }
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/me", response_model=dict)
async def delete_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Delete current user's profile
    
    Removes the user profile permanently.
    Requires authentication.
    """
    try:
        result = await delete_user_profile(str(current_user["_id"]))
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=dict)
async def delete_user_profile_by_id(user_id: str):
    """Delete user profile by ID (admin only)"""
    try:
        result = await delete_user_profile(user_id)
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

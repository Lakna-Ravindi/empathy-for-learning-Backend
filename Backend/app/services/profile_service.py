# app/services/profile_service.py
from bson import ObjectId
from app.db.database import users_collection
from app.models.profile_models import ProfileUpdate
from app.core.validators import ValidationError


async def update_user_profile(user_id: str, profile_data: ProfileUpdate) -> dict:
    """Update user profile with age group"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise ValidationError("Invalid user ID format")
        
        # Build update data - only include fields that are not None
        update_dict = {}
        if profile_data.ageGroup is not None:
            update_dict["ageGroup"] = profile_data.ageGroup
        
        # If no fields to update
        if not update_dict:
            raise ValidationError("No fields provided for update")
        
        # Update user in database
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise ValidationError("User not found")
        
        # Fetch and return updated user
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if updated_user:
            updated_user["id"] = str(updated_user["_id"])
            del updated_user["_id"]
            del updated_user["password"]  # Don't return password
        
        return updated_user
    
    except Exception as e:
        raise ValidationError(str(e))


async def delete_user_profile(user_id: str) -> dict:
    """Delete user profile"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise ValidationError("Invalid user ID format")
        
        # Delete user from database
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise ValidationError("User not found")
        
        return {"message": "User profile deleted successfully", "userId": user_id}
    
    except Exception as e:
        raise ValidationError(str(e))


async def get_user_profile(user_id: str) -> dict:
    """Get user profile"""
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            raise ValidationError("Invalid user ID format")
        
        # Fetch user from database
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise ValidationError("User not found")
        
        user["id"] = str(user["_id"])
        del user["_id"]
        del user["password"]  # Don't return password
        
        return user
    
    except Exception as e:
        raise ValidationError(str(e))

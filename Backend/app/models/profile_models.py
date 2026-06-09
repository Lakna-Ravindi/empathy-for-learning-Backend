# app/models/profile_models.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgeGroupEnum(str, Enum):
    """Age group options"""
    BELOW_16 = "Below 16 years"
    AGE_16_18 = "16–18 years"
    AGE_19_21 = "19–21 years"
    AGE_22_25 = "22-25 years"
    AGE_26_PLUS = "26+ years"


class ProfileCreate(BaseModel):
    """Profile creation model"""
    ageGroup: AgeGroupEnum = Field(..., description="Age group")


class ProfileUpdate(BaseModel):
    """Profile update model"""
    ageGroup: Optional[AgeGroupEnum] = None


class ProfileResponse(BaseModel):
    """Profile response model"""
    ageGroup: AgeGroupEnum

    class Config:
        from_attributes = True

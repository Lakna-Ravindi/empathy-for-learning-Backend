# app/models/user_models.py
from pydantic import BaseModel, Field, field_validator
from app.core.validators import validate_password
from enum import Enum


class AgeGroupEnum(str, Enum):
    """Age group options"""
    BELOW_16 = "Below 16 years"
    AGE_16_18 = "16–18 years"
    AGE_19_21 = "19–21 years"
    AGE_22_25 = "22-25 years"
    AGE_26_PLUS = "26+ years"


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username for login")
    password: str = Field(..., min_length=8, description="Must include uppercase, lowercase, numbers, and symbols")
    ageGroup: AgeGroupEnum = Field(..., description="Age group")
    privacyConsent: bool = Field(..., description="Must be true to register")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        validate_password(v)
        return v

    @field_validator("privacyConsent")
    @classmethod
    def check_privacy_consent(cls, v):
        if not v:
            raise ValueError("Privacy consent must be accepted to register")
        return v


class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    username: str
    ageGroup: AgeGroupEnum

    class Config:
        from_attributes = True
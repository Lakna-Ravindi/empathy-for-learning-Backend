from pydantic import BaseModel
from typing import Optional


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str


class TokenPayload(BaseModel):
    """JWT token payload"""
    username: str
    role: str
    type: str  # "access" or "refresh"
    exp: Optional[int] = None


class CurrentUser(BaseModel):
    """Current authenticated user model"""
    username: str
    role: str
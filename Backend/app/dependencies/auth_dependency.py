# app/dependencies/auth_dependency.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import logging
from app.core.security import verify_token
from app.models.auth_models import CurrentUser
from app.db.database import revoked_tokens_collection

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(credentials = Depends(security)) -> CurrentUser:
    """
    Dependency to extract and verify JWT token from request headers.
    Returns the current authenticated user.
    Raises HTTPException if token is invalid, expired, or revoked.
    """
    token = credentials.credentials

    # Verify token signature and expiration
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is revoked
    revoked = revoked_tokens_collection.find_one({"token": token})
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type is "access"
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning(f"Non-access token used for authentication: {token_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("username")
    role = payload.get("role")

    if not username or not role:
        logger.warning("Token payload missing required fields")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(username=username, role=role)


async def get_current_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency for admin-only routes.
    Verifies that the current user has admin role.
    """
    if current_user.role != "admin":
        logger.warning(f"Non-admin user attempted admin action: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[object] = Depends(security),
) -> Optional[CurrentUser]:
    """
    Optional dependency for routes that don't require authentication.
    Returns current user if token is valid, None otherwise.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        return None

    # Check if token is revoked
    revoked = revoked_tokens_collection.find_one({"token": token})
    if revoked:
        return None

    email = payload.get("email")
    role = payload.get("role")

    if email and role:
        return CurrentUser(email=email, role=role)

    return None

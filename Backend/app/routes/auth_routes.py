# app/routes/auth_routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user_models import UserRegister, UserResponse
from app.models.auth_models import UserLogin, TokenResponse, TokenRefreshRequest, CurrentUser
from app.services.auth_service import register_user, login_user, refresh_access_token, logout_user
from app.dependencies.auth_dependency import get_current_user
from app.core.validators import ValidationError

router = APIRouter()


@router.post("/register", response_model=dict)
def register(user: UserRegister):
    """Register a new user with validation"""
    try:
        success, message = register_user(user.dict())

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {"message": message, "status": "success"}

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during registration")


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    """Login user and return access and refresh tokens"""
    try:
        tokens, db_user = login_user(user.username, user.password)

        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=db_user,  # db_user contains the error message
            )

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during login")


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: TokenRefreshRequest):
    """Refresh access token using refresh token"""
    try:
        new_access_token, message = refresh_access_token(request.refresh_token)

        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message,
            )

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during token refresh")


@router.post("/logout", response_model=dict)
def logout(current_user: CurrentUser = Depends(get_current_user), request = None):
    """Logout user and revoke token"""
    try:
        # Note: Token revocation is tracked in the database
        # The actual token extraction happens in get_current_user dependency
        # For full logout, the client should discard the token
        success, message = logout_user("", current_user.username)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {"message": message, "status": "success"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during logout")


@router.get("/me", response_model=dict)
def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user info"""
    return {
        "username": current_user.username,
        "role": current_user.role,
    }
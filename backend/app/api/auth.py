"""
Authentication REST API Endpoints.

Handles user registration, login, logout, password recovery, session verification,
and ephemeral guest sessions with HttpOnly cookies and Bearer tokens.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.services.auth_service import AuthService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def set_auth_cookie(response: Response, token: str, remember_me: bool = False):
    """Set secure HttpOnly authentication cookie."""
    max_age = 30 * 24 * 3600 if remember_me else 24 * 3600
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=False,  # Set True in production with HTTPS
        path="/",
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers user with password policy verification and sets secure session.",
)
async def register(request: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Register a new user account."""
    token_resp = AuthService.register_user(db, request)
    set_auth_cookie(response, token_resp.access_token)
    return token_resp


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login & session issuance",
    description="Authenticates credentials, protects against brute-force attacks, and sets session.",
)
async def login(
    request: UserLoginRequest,
    raw_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user credentials."""
    client_ip = raw_request.client.host if raw_request.client else "unknown"
    token_resp = AuthService.authenticate_user(db, request, client_identifier=client_ip)
    set_auth_cookie(response, token_resp.access_token, remember_me=request.remember_me)
    return token_resp


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Clears authentication cookie and terminates current session.",
)
async def logout(response: Response):
    """Log out user by clearing authentication cookie."""
    response.delete_cookie(key="access_token", path="/")
    return MessageResponse(success=True, message="Successfully logged out.")


@router.post(
    "/guest",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate guest evaluation session",
    description="Creates an ephemeral guest session for immediate platform exploration.",
)
async def guest_session(response: Response, db: Session = Depends(get_db)):
    """Create an ephemeral guest session."""
    token_resp = AuthService.create_guest_user(db)
    set_auth_cookie(response, token_resp.access_token)
    return token_resp


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns authenticated user profile information.",
)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Retrieve profile of currently authenticated user."""
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_guest=user.is_guest,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password recovery token",
    description="Generates a cryptographically secure password reset token with 30-minute expiry.",
)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset."""
    resp, _ = AuthService.request_password_reset(db, request.email)
    return resp


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with recovery token",
    description="Validates single-use token and updates password.",
)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using secure token."""
    return AuthService.reset_password(db, request)

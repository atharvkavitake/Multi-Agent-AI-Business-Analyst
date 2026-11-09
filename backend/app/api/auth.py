"""
Authentication REST API Endpoints.

Handles user registration, login, JWT token issuance, profile retrieval,
and ephemeral guest evaluation sessions.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.services.auth_service import AuthService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new user, hashes password via bcrypt, and returns a signed JWT access token.",
)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    return AuthService.register_user(db, request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login & token issuance",
    description="Authenticates credentials and returns a signed JWT access token.",
)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials."""
    return AuthService.authenticate_user(db, request)


@router.post(
    "/guest",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate guest evaluation session",
    description="Creates an ephemeral guest user account allowing immediate exploration without registration.",
)
async def guest_session(db: Session = Depends(get_db)):
    """Create an ephemeral guest session."""
    return AuthService.create_guest_user(db)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Decodes JWT bearer token and retrieves authenticated user information.",
)
async def get_current_user(
    authorization: str = Header(..., description="Bearer JWT token"),
    db: Session = Depends(get_db),
):
    """Retrieve profile of currently authenticated user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '.",
        )
    token = authorization.replace("Bearer ", "").strip()
    user = AuthService.get_current_user_from_token(db, token)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_guest=user.is_guest,
        created_at=user.created_at.isoformat(),
    )


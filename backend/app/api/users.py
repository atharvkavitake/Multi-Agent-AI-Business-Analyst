"""
User Profile REST API Endpoints.

Handles user profile retrieval, full name updates, password changes,
and permanent account deletion.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    MessageResponse,
    UserProfileUpdateRequest,
    UserResponse,
)
from backend.app.services.auth_service import AuthService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get user profile",
    description="Returns detailed profile information for the authenticated user.",
)
async def get_profile(user: User = Depends(get_current_user)):
    """Retrieve active user's profile."""
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


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update profile name",
    description="Updates user's display name.",
)
async def update_profile(
    request: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user full name."""
    return AuthService.update_profile(db, user, request)


@router.put(
    "/change-password",
    response_model=MessageResponse,
    summary="Change account password",
    description="Validates current password and sets a new strong password.",
)
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change account password."""
    return AuthService.change_password(db, user, request)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete account permanently",
    description="Requires password verification and permanently deletes account, datasets, and history.",
)
async def delete_account(
    request: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete user account."""
    return AuthService.delete_account(db, user, request.password)

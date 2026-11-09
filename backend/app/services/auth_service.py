"""
Authentication & User Management Service.

Handles user registration, credential authentication, guest sessions,
and JWT token generation.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.utils.logging_config import get_logger
from backend.app.utils.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

logger = get_logger(__name__)


class AuthService:
    """Authentication and session management service."""

    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> TokenResponse:
        """Register a new user account with hashed password and return JWT."""
        # Check if username or email already exists
        existing = db.query(User).filter(
            (User.email == request.email.lower()) | (User.username == request.username)
        ).first()

        if existing:
            if existing.email.lower() == request.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email address already exists.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )

        hashed_pw = get_password_hash(request.password)
        new_user = User(
            id=str(uuid.uuid4()),
            username=request.username.strip(),
            email=request.email.lower().strip(),
            password_hash=hashed_pw,
            is_active=True,
            is_guest=False,
            created_at=datetime.utcnow(),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User registered successfully: '{new_user.username}' ({new_user.id})")

        token = create_access_token(data={"sub": new_user.id, "username": new_user.username})
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                is_active=new_user.is_active,
                is_guest=new_user.is_guest,
                created_at=new_user.created_at.isoformat(),
            ),
        )

    @staticmethod
    def authenticate_user(db: Session, request: UserLoginRequest) -> TokenResponse:
        """Authenticate user by username or email and password."""
        ident = request.username_or_email.strip().lower()
        user = db.query(User).filter(
            (User.email == ident) | (User.username.ilike(ident))
        ).first()

        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        token = create_access_token(data={"sub": user.id, "username": user.username})
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_guest=user.is_guest,
                created_at=user.created_at.isoformat(),
            ),
        )

    @staticmethod
    def create_guest_user(db: Session) -> TokenResponse:
        """Create an ephemeral guest user session for seamless evaluation."""
        guest_id = str(uuid.uuid4())
        short_id = guest_id[:8]
        guest_user = User(
            id=guest_id,
            username=f"guest_{short_id}",
            email=f"guest_{short_id}@ephemeral.local",
            password_hash=get_password_hash(str(uuid.uuid4())),
            is_active=True,
            is_guest=True,
            created_at=datetime.utcnow(),
        )

        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)

        logger.info(f"Guest session created: '{guest_user.username}'")

        token = create_access_token(data={"sub": guest_user.id, "username": guest_user.username, "guest": True})
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=guest_user.id,
                username=guest_user.username,
                email=guest_user.email,
                is_active=guest_user.is_active,
                is_guest=True,
                created_at=guest_user.created_at.isoformat(),
            ),
        )

    @staticmethod
    def get_current_user_from_token(db: Session, token: str) -> User:
        """Validate JWT token and retrieve corresponding User record."""
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload["sub"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user


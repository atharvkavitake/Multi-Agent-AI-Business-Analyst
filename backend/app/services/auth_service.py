"""
Authentication & User Management Service.

Handles registration with password policy enforcement, credential authentication
with brute-force protection, password recovery tokens, profile management,
and account deletion.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.password_reset import PasswordReset
from backend.app.models.user import User
from backend.app.schemas.user import (
    ChangePasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.utils.logging_config import get_logger
from backend.app.utils.security import (
    check_login_rate_limit,
    create_access_token,
    decode_access_token,
    generate_secure_token,
    get_password_hash,
    hash_token,
    record_failed_login,
    reset_failed_login,
    validate_password_strength,
    verify_password,
)

logger = get_logger(__name__)
settings = get_settings()


class AuthService:
    """Enterprise authentication and session management service."""

    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> TokenResponse:
        """
        Register a new user account with strict password policy verification
        and email uniqueness check.
        """
        clean_email = request.email.lower().strip()

        # 1. Enforce password strength policy
        is_strong, err_msg = validate_password_strength(request.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )

        # 2. Check if email already registered
        existing_user = db.query(User).filter(User.email == clean_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists. Please log in.",
            )

        # 3. Create new user record
        hashed_pw = get_password_hash(request.password)
        new_user = User(
            id=str(uuid.uuid4()),
            full_name=request.full_name.strip(),
            email=clean_email,
            hashed_password=hashed_pw,
            is_active=True,
            is_verified=True,
            is_guest=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User registered successfully: '{new_user.full_name}' <{new_user.email}> (ID: {new_user.id})")

        # 4. Generate access token
        token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email, "name": new_user.full_name}
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=new_user.id,
                full_name=new_user.full_name,
                email=new_user.email,
                is_active=new_user.is_active,
                is_verified=new_user.is_verified,
                is_guest=new_user.is_guest,
                created_at=new_user.created_at.isoformat(),
                last_login=new_user.last_login.isoformat() if new_user.last_login else None,
            ),
        )

    @staticmethod
    def authenticate_user(
        db: Session, request: UserLoginRequest, client_identifier: str = "unknown"
    ) -> TokenResponse:
        """
        Authenticate user credentials with brute-force rate-limiting protection.
        """
        ident = (request.email or request.username_or_email or "").strip().lower()

        # 1. Check brute-force lockout
        is_locked, remaining_sec = check_login_rate_limit(ident)
        if not is_locked:
            is_locked, remaining_sec = check_login_rate_limit(client_identifier)

        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Account temporarily locked. Please try again in {remaining_sec} seconds.",
            )

        # 2. Query user by email
        user = db.query(User).filter(User.email == ident).first()

        # Fallback check on username/full_name if older client
        if not user:
            user = db.query(User).filter(User.full_name.ilike(ident)).first()

        if not user or not verify_password(request.password, user.hashed_password):
            record_failed_login(ident)
            record_failed_login(client_identifier)
            logger.warning(f"Failed login attempt for identifier: '{ident}' from '{client_identifier}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is currently inactive. Please contact support.",
            )

        # 3. Successful login - clear rate-limit trackers & update timestamp
        reset_failed_login(ident)
        reset_failed_login(client_identifier)

        user.last_login = datetime.utcnow()
        db.commit()

        # 4. Determine token expiration
        expires_delta = timedelta(days=30) if request.remember_me else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": user.id, "email": user.email, "name": user.full_name},
            expires_delta=expires_delta,
        )

        logger.info(f"User authenticated: '{user.full_name}' <{user.email}>")

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                is_verified=user.is_verified,
                is_guest=user.is_guest,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None,
            ),
        )

    @staticmethod
    def create_guest_user(db: Session) -> TokenResponse:
        """Create an ephemeral guest user session for recruiter exploration."""
        guest_id = str(uuid.uuid4())
        short_id = guest_id[:8]
        guest_user = User(
            id=guest_id,
            full_name=f"guest_{short_id}",
            email=f"guest_{short_id}@demo.bi-platform.local",
            hashed_password=get_password_hash(str(uuid.uuid4())),
            is_active=True,
            is_verified=True,
            is_guest=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
        )

        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)

        logger.info(f"Ephemeral guest session created: '{guest_user.full_name}'")

        token = create_access_token(
            data={"sub": guest_user.id, "email": guest_user.email, "name": guest_user.full_name, "guest": True}
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=guest_user.id,
                full_name=guest_user.full_name,
                email=guest_user.email,
                is_active=guest_user.is_active,
                is_verified=True,
                is_guest=True,
                created_at=guest_user.created_at.isoformat(),
                last_login=guest_user.last_login.isoformat(),
            ),
        )

    @staticmethod
    def request_password_reset(db: Session, email: str) -> Tuple[MessageResponse, Optional[str]]:
        """
        Generate a cryptographically secure password reset token and store its hash.
        Returns generic response to prevent email enumeration, plus dev reset token for local test.
        """
        clean_email = email.lower().strip()
        user = db.query(User).filter(User.email == clean_email).first()

        raw_token = None
        if user and user.is_active:
            raw_token = generate_secure_token()
            t_hash = hash_token(raw_token)
            expires = datetime.utcnow() + timedelta(minutes=30)

            # Invalidate any existing unused reset tokens for this user
            db.query(PasswordReset).filter(
                PasswordReset.user_id == user.id,
                PasswordReset.used_at.is_(None),
            ).update({"used_at": datetime.utcnow()})

            reset_record = PasswordReset(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=t_hash,
                expires_at=expires,
                created_at=datetime.utcnow(),
            )
            db.add(reset_record)
            db.commit()

            # Local dev logging: safe link for development verification
            reset_url = f"/app/reset-password.html?token={raw_token}"
            logger.info(f"[PASSWORD RECOVERY] Generated reset link for '{clean_email}': {reset_url}")

        return MessageResponse(
            success=True,
            message="If your email address is registered, password recovery instructions have been sent.",
            detail=f"Development reset token: {raw_token}" if raw_token else None,
        ), raw_token

    @staticmethod
    def reset_password(db: Session, request: ResetPasswordRequest) -> MessageResponse:
        """
        Validate password reset token and update user credentials.
        """
        t_hash = hash_token(request.token.strip())
        now = datetime.utcnow()

        reset_record = db.query(PasswordReset).filter(
            PasswordReset.token_hash == t_hash,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > now,
        ).first()

        if not reset_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token is invalid, already used, or expired.",
            )

        # Enforce password strength
        is_strong, err_msg = validate_password_strength(request.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )

        user = db.query(User).filter(User.id == reset_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated user account not found.",
            )

        user.hashed_password = get_password_hash(request.new_password)
        user.updated_at = datetime.utcnow()
        reset_record.used_at = datetime.utcnow()

        db.commit()
        logger.info(f"Password reset successfully completed for user: '{user.email}'")

        return MessageResponse(
            success=True,
            message="Your password has been reset successfully. You can now log in.",
        )

    @staticmethod
    def update_profile(
        db: Session, user: User, request: UserProfileUpdateRequest
    ) -> UserResponse:
        """Update user profile information."""
        user.full_name = request.full_name.strip()
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        logger.info(f"User profile updated: ID={user.id}, Name='{user.full_name}'")

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

    @staticmethod
    def change_password(
        db: Session, user: User, request: ChangePasswordRequest
    ) -> MessageResponse:
        """Change user password after verifying current password."""
        if not verify_password(request.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password entered is incorrect.",
            )

        is_strong, err_msg = validate_password_strength(request.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )

        user.hashed_password = get_password_hash(request.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"User changed password successfully: ID={user.id}")

        return MessageResponse(
            success=True,
            message="Password successfully changed.",
        )

    @staticmethod
    def delete_account(db: Session, user: User, password: str) -> MessageResponse:
        """Delete user account and all associated datasets and analyses."""
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation is incorrect. Account deletion aborted.",
            )

        user_id = user.id
        db.delete(user)
        db.commit()

        logger.info(f"User account deleted: ID={user_id}")

        return MessageResponse(
            success=True,
            message="Your account and all associated analysis records have been permanently deleted.",
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
                detail="User account not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

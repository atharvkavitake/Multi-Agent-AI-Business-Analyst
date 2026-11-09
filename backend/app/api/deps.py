"""
FastAPI Reusable Dependencies.

Provides secure user authentication via Bearer JWT tokens, HttpOnly session cookies,
and optional download tokens, with strict database session management.
"""

from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.utils.logging_config import get_logger
from backend.app.utils.security import decode_access_token

logger = get_logger(__name__)


def extract_token(
    authorization: Optional[str] = Header(None, description="Bearer token"),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    token_query: Optional[str] = Query(None, alias="token"),
) -> Optional[str]:
    """
    Extract JWT token from Authorization header, HttpOnly cookie, or query parameter.
    """
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "").strip()
    if access_token_cookie:
        return access_token_cookie.strip()
    if token_query:
        return token_query.strip()
    return None


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency verifying authentication and yielding the active User model.
    Rejects missing, forged, or expired credentials with HTTP 401.
    """
    raw_token = extract_token(authorization, access_token, token)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated.",
        )

    return user


async def get_optional_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional dependency returning User if authenticated, or None if anonymous.
    """
    try:
        return await get_current_user(request, authorization, access_token, token, db)
    except HTTPException:
        return None


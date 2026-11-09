"""
Security & Cryptography Utilities.

Provides bcrypt password hashing, verification, password strength auditing,
cryptographic token generation for password resets, JWT token issuance/decoding,
and in-memory brute-force rate-limiting.
"""

from datetime import datetime, timedelta
import hashlib
import re
import secrets
from typing import Any, Dict, Optional, Tuple
import bcrypt
from jose import JWTError, jwt

from backend.app.config import get_settings
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# In-memory store for tracking failed login attempts: {identifier: [timestamp1, timestamp2, ...]}
_FAILED_LOGIN_ATTEMPTS: Dict[str, list] = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes
LOCKOUT_DURATION_SECONDS = 300   # 5 minutes lockout


def get_password_hash(password: str) -> str:
    """Hash plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets enterprise security policy:
    - At least 8 characters
    - At least one uppercase character
    - At least one lowercase character
    - At least one digit
    - At least one special symbol
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\/`~]", password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."
    return True, None


def generate_secure_token() -> str:
    """Generate a cryptographically random, URL-safe token for password resets."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Generate SHA256 hex digest of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def check_login_rate_limit(key: str) -> Tuple[bool, int]:
    """
    Check if an identifier (IP address or email) is temporarily locked out.
    Returns (is_locked, seconds_remaining).
    """
    now = datetime.utcnow()
    attempts = _FAILED_LOGIN_ATTEMPTS.get(key, [])

    # Filter attempts within the window
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    valid_attempts = [t for t in attempts if t > cutoff]
    _FAILED_LOGIN_ATTEMPTS[key] = valid_attempts

    if len(valid_attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
        newest = max(valid_attempts)
        elapsed = (now - newest).total_seconds()
        remaining = int(LOCKOUT_DURATION_SECONDS - elapsed)
        if remaining > 0:
            return True, remaining

    return False, 0


def record_failed_login(key: str):
    """Record a failed login attempt for an identifier."""
    now = datetime.utcnow()
    if key not in _FAILED_LOGIN_ATTEMPTS:
        _FAILED_LOGIN_ATTEMPTS[key] = []
    _FAILED_LOGIN_ATTEMPTS[key].append(now)


def reset_failed_login(key: str):
    """Clear failed login attempts upon successful authentication."""
    if key in _FAILED_LOGIN_ATTEMPTS:
        del _FAILED_LOGIN_ATTEMPTS[key]


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate signature/expiration of JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None

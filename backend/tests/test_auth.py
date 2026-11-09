"""
Unit and Integration Tests for User Authentication, Password Hashing, and JWT Tokens.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.utils.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client managing lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def test_password_hashing_and_verification():
    """Verify bcrypt password hashing and constant-time comparison."""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Verify signed JWT token issuance and signature verification."""
    payload = {"sub": "user-uuid-123", "username": "analyst_bob"}
    token = create_access_token(payload)

    assert token is not None
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-123"
    assert decoded["username"] == "analyst_bob"


def test_user_registration_and_login_lifecycle(client):
    """
    Test full auth flow: Register -> Login -> Profile /me -> Rejection cases.
    """
    unique_suffix = str(uuid.uuid4())[:8]
    username = f"analyst_{unique_suffix}"
    email = f"analyst_{unique_suffix}@enterprise.com"
    password = "TestPassword99!"

    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["username"] == username
    assert reg_data["user"]["is_guest"] is False

    token = reg_data["access_token"]

    # 2. Duplicate registration should fail
    dup_resp = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 3. Login with correct credentials
    login_resp = client.post(
        "/api/auth/login",
        json={"username_or_email": email, "password": password},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Login with invalid password should fail with 401
    bad_login_resp = client.post(
        "/api/auth/login",
        json={"username_or_email": email, "password": "BadPassword123"},
    )
    assert bad_login_resp.status_code == 401

    # 5. Access protected /api/auth/me profile with Bearer token
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == username
    assert me_data["email"] == email


def test_guest_session_generation(client):
    """Verify ephemeral guest session creation for instant exploration."""
    guest_resp = client.post("/api/auth/guest")
    assert guest_resp.status_code == 201
    data = guest_resp.json()

    assert "access_token" in data
    assert data["user"]["is_guest"] is True
    assert data["user"]["username"].startswith("guest_")

    guest_token = data["access_token"]

    # Verify guest token works on protected endpoint
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["is_guest"] is True

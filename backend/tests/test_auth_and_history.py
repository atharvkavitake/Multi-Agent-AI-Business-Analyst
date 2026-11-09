"""
Comprehensive Integration Tests for User Authentication, Account Security,
Personalized Analysis History, and Multi-Tenant Isolation.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.utils.security import _FAILED_LOGIN_ATTEMPTS, reset_failed_login


@pytest.fixture(scope="module")
def client():
    """Module-scoped test client managing FastAPI lifespan."""
    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------------------------------
# 1. User Registration Scenarios
# --------------------------------------------------------------------------

def test_user_registration_success(client):
    """Test successful user registration with valid details."""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "full_name": f"Senior Analyst {uid}",
        "email": f"analyst_{uid}@enterprise.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["full_name"] == payload["full_name"]
    assert data["user"]["email"] == payload["email"].lower()
    assert data["user"]["is_guest"] is False


def test_user_registration_duplicate_email(client):
    """Test that registering an already registered email is rejected."""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "full_name": f"Duplicate User {uid}",
        "email": f"dup_{uid}@enterprise.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    first_resp = client.post("/api/auth/register", json=payload)
    assert first_resp.status_code == 201

    # Second registration with same email
    second_resp = client.post("/api/auth/register", json=payload)
    assert second_resp.status_code == 400
    assert "already exists" in second_resp.json()["detail"]


def test_user_registration_weak_password(client):
    """Test that registering with a short/weak password fails."""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "full_name": f"Weak Pwd User {uid}",
        "email": f"weak_{uid}@enterprise.com",
        "password": "123",
        "confirm_password": "123",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code in (400, 422)


def test_user_registration_mismatched_password(client):
    """Test that mismatched passwords fail validation."""
    uid = str(uuid.uuid4())[:8]
    payload = {
        "full_name": f"Mismatch User {uid}",
        "email": f"mismatch_{uid}@enterprise.com",
        "password": "StrongPassword123!",
        "confirm_password": "DifferentPassword456!",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code in (400, 422)


# --------------------------------------------------------------------------
# 2. Login, Brute-Force Rate Limiting & Guest Mode
# --------------------------------------------------------------------------

def test_login_success_and_guest_mode(client):
    """Verify login authentication and instant guest demo session issuance."""
    uid = str(uuid.uuid4())[:8]
    email = f"login_test_{uid}@enterprise.com"
    pwd = "ValidPassword123!"

    # Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"full_name": "Login Tester", "email": email, "password": pwd},
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": pwd},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Guest session creation
    guest_resp = client.post("/api/auth/guest")
    assert guest_resp.status_code == 201
    guest_data = guest_resp.json()
    assert guest_data["user"]["is_guest"] is True


def test_login_invalid_credentials_and_rate_limit(client):
    """Verify invalid credentials return 401 and consecutive failures trigger rate limit lockout."""
    uid = str(uuid.uuid4())[:8]
    email = f"brute_{uid}@enterprise.com"
    pwd = "CorrectPassword123!"

    client.post(
        "/api/auth/register",
        json={"full_name": "Brute Tester", "email": email, "password": pwd},
    )

    # Clean in-memory tracker for this test email and testclient
    reset_failed_login(email.lower())
    reset_failed_login("testclient")

    # 4 bad attempts
    for _ in range(4):
        bad_resp = client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword!"},
        )
        assert bad_resp.status_code == 401

    # 5th bad attempt
    fifth_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert fifth_resp.status_code == 401

    # 6th attempt should be blocked by rate limiting (429 Too Many Requests)
    locked_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": pwd},
    )
    assert locked_resp.status_code == 429
    assert "locked" in locked_resp.json()["detail"].lower()

    # Clean up tracker
    reset_failed_login(email.lower())
    reset_failed_login("testclient")


# --------------------------------------------------------------------------
# 3. Password Reset Lifecycle
# --------------------------------------------------------------------------

def test_password_reset_lifecycle(client):
    """Test full password reset flow: request -> verify -> reset -> token reuse block."""
    uid = str(uuid.uuid4())[:8]
    email = f"reset_{uid}@enterprise.com"
    old_pwd = "OriginalPassword123!"
    new_pwd = "BrandNewPassword456!"

    # Register
    client.post(
        "/api/auth/register",
        json={"full_name": "Reset Tester", "email": email, "password": old_pwd},
    )

    # Request reset
    req_resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert req_resp.status_code == 200
    req_data = req_resp.json()
    assert req_data["success"] is True

    # Extract dev token
    assert req_data["detail"] is not None and "Development reset token:" in req_data["detail"]
    token = req_data["detail"].split("Development reset token:")[1].strip()

    # Attempt reset with invalid token
    bad_reset = client.post(
        "/api/auth/reset-password",
        json={"token": "invalid_token_12345", "new_password": new_pwd, "confirm_password": new_pwd},
    )
    assert bad_reset.status_code == 400

    # Successful reset with valid token
    good_reset = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": new_pwd, "confirm_password": new_pwd},
    )
    assert good_reset.status_code == 200
    assert good_reset.json()["success"] is True

    # Attempt to reuse the same token (Must be blocked)
    reuse_resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "ThirdPassword789!", "confirm_password": "ThirdPassword789!"},
    )
    assert reuse_resp.status_code == 400

    # Verify login with new password works
    login_new = client.post(
        "/api/auth/login",
        json={"email": email, "password": new_pwd},
    )
    assert login_new.status_code == 200


# --------------------------------------------------------------------------
# 4. User Profile & Account Management
# --------------------------------------------------------------------------

def test_user_profile_and_account_management(client):
    """Verify profile updating, password change, and permanent account deletion."""
    uid = str(uuid.uuid4())[:8]
    email = f"profile_{uid}@enterprise.com"
    pwd = "CurrentPassword123!"

    reg = client.post(
        "/api/auth/register",
        json={"full_name": "Initial Name", "email": email, "password": pwd},
    ).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update Full Name
    update_resp = client.put(
        "/api/users/me",
        json={"full_name": "Updated Full Name"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["full_name"] == "Updated Full Name"

    # 2. Change Password
    new_pwd = "ChangedPassword999!"
    change_resp = client.put(
        "/api/users/change-password",
        json={
            "current_password": pwd,
            "new_password": new_pwd,
            "confirm_password": new_pwd,
        },
        headers=headers,
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["success"] is True

    # 3. Delete Account with wrong password
    bad_delete = client.request(
        "DELETE",
        "/api/users/me",
        json={"password": "WrongPassword!"},
        headers=headers,
    )
    assert bad_delete.status_code == 400

    # 4. Delete Account with correct new password
    good_delete = client.request(
        "DELETE",
        "/api/users/me",
        json={"password": new_pwd},
        headers=headers,
    )
    assert good_delete.status_code == 200
    assert good_delete.json()["success"] is True

    # 5. Subsequent access should be unauthorized / not found
    after_me = client.get("/api/auth/me", headers=headers)
    assert after_me.status_code in (401, 404)


# --------------------------------------------------------------------------
# 5. Multi-Tenant Personalized Analysis History & Isolation
# --------------------------------------------------------------------------

def test_personalized_history_and_cross_user_isolation(client):
    """
    Crucial Test:
    User A uploads dataset and runs analysis -> session saved in User A's history.
    User B registers and checks history -> empty history.
    User B attempts to view or delete User A's analysis -> 403 Forbidden!
    """
    uid_a = str(uuid.uuid4())[:8]
    uid_b = str(uuid.uuid4())[:8]

    # User A setup
    user_a_email = f"user_a_{uid_a}@enterprise.com"
    pwd_a = "UserAPassword123!"
    reg_a = client.post(
        "/api/auth/register",
        json={"full_name": "User Alpha", "email": user_a_email, "password": pwd_a},
    ).json()
    token_a = reg_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B setup
    user_b_email = f"user_b_{uid_b}@enterprise.com"
    pwd_b = "UserBPassword123!"
    reg_b = client.post(
        "/api/auth/register",
        json={"full_name": "User Beta", "email": user_b_email, "password": pwd_b},
    ).json()
    token_b = reg_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a dataset
    csv_content = (
        "Date,Region,Product,Revenue,Cost\n"
        "2026-01-01,North,Widget,1000,600\n"
        "2026-01-02,South,Widget,1500,800\n"
        "2026-01-03,East,Gadget,2000,1100\n"
        "2026-01-04,West,Gadget,2500,1200\n"
    )
    upload_resp = client.post(
        "/api/datasets/upload",
        files={"file": ("alpha_sales.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=headers_a,
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["dataset_id"]

    # User A runs analysis
    analysis_resp = client.post(
        f"/api/analysis/{dataset_id}/run",
        headers=headers_a,
    )
    assert analysis_resp.status_code == 200
    analysis_id = analysis_resp.json()["analysis_id"]

    # User A queries their history
    history_a = client.get("/api/history", headers=headers_a)
    assert history_a.status_code == 200
    data_a = history_a.json()
    assert data_a["total_count"] >= 1
    found = any(item["analysis_id"] == analysis_id for item in data_a["items"])
    assert found is True

    # User B queries their history -> must NOT contain User A's analysis!
    history_b = client.get("/api/history", headers=headers_b)
    assert history_b.status_code == 200
    data_b = history_b.json()
    assert data_b["total_count"] == 0
    assert len(data_b["items"]) == 0

    # User B attempts to access User A's analysis detail -> 403 Forbidden
    detail_b = client.get(f"/api/history/{analysis_id}", headers=headers_b)
    assert detail_b.status_code == 403

    # User B attempts to delete User A's analysis -> 403 Forbidden
    delete_b = client.delete(f"/api/history/{analysis_id}", headers=headers_b)
    assert delete_b.status_code == 403

    # User A can access detail and delete their own analysis
    detail_a = client.get(f"/api/history/{analysis_id}", headers=headers_a)
    assert detail_a.status_code == 200
    assert detail_a.json()["analysis_id"] == analysis_id

    delete_a = client.delete(f"/api/history/{analysis_id}", headers=headers_a)
    assert delete_a.status_code == 200
    assert delete_a.json()["success"] is True

    # After deletion, User A's history is empty again
    history_after = client.get("/api/history", headers=headers_a).json()
    assert any(item["analysis_id"] == analysis_id for item in history_after["items"]) is False

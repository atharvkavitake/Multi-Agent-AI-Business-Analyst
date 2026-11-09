"""
User Authentication, Profile & Password Recovery Schemas.

Type-safe Pydantic V2 schemas for registration, credential verification,
profile updates, and secure token lifecycle.
"""

from typing import Optional
from pydantic import BaseModel, Field, computed_field, model_validator


class UserRegisterRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User's full name")
    username: Optional[str] = Field(None, min_length=2, max_length=100, description="Username alias")
    email: str = Field(..., pattern=r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    confirm_password: Optional[str] = Field(None, min_length=8, max_length=128, description="Password confirmation")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if not self.full_name and not self.username:
            raise ValueError("Full Name is required.")
        if not self.full_name and self.username:
            self.full_name = self.username
        if self.confirm_password and self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UserLoginRequest(BaseModel):
    email: Optional[str] = None
    username_or_email: Optional[str] = None
    password: str = Field(..., min_length=1, description="Account password")
    remember_me: bool = False

    @model_validator(mode="after")
    def normalize_identifier(self):
        ident = self.email or self.username_or_email
        if not ident:
            raise ValueError("Email address is required.")
        self.email = ident.strip().lower()
        self.username_or_email = self.email
        return self


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", description="Registered email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New strong password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match.")
        return self


class UserProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Updated full name")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New strong password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match.")
        return self


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password confirmation to delete account")


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool
    is_verified: bool = True
    is_guest: bool = False
    created_at: str
    last_login: Optional[str] = None

    # Compatibility alias for username
    @computed_field
    @property
    def username(self) -> str:
        return self.full_name

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    success: bool
    message: str
    detail: Optional[str] = None

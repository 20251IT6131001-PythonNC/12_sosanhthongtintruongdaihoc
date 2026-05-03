"""
Pydantic schemas for Authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response after login"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Schema for refreshed access token response"""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class SendVerificationCodeRequest(BaseModel):
    """Schema for sending verification code"""
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class SendVerificationCodeResponse(BaseModel):
    """Schema for verification code response"""
    message: str
    email: str


class VerifyCodeRequest(BaseModel):
    """Schema for verifying code during signup"""
    email: EmailStr
    code: str

class VerifyCodeResponse(BaseModel):
    """Schema for verification code response"""
    message: str


class ForgotPasswordSendCodeRequest(BaseModel):
    """Schema for sending forgot password code"""
    email: EmailStr


class ForgotPasswordResetRequest(BaseModel):
    """Schema for resetting password"""
    email: EmailStr
    code: str
    new_password: str
    confirm_password: str

"""
Authentication API routes.
Handles signup, login, token refresh, and logout.
"""
from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import (
    LoginRequest,
    Token,
    TokenRefresh,
    AccessTokenResponse,
    MessageResponse,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    ForgotPasswordSendCodeRequest,
    ForgotPasswordResetRequest
)
from app.schemas.user import UserResponse
from app.models.user import UserModel
from app.models.study_bg import StudyBGModel
from app.utils.security import verify_password
from app.utils.auth import create_access_token, create_refresh_token, verify_token
from app.utils.email import send_verification_code_email
from app.database import execute_query, get_db
from app.utils.rate_limit import limiter
from datetime import datetime, timedelta
from app.config import settings
import random
import string

router = APIRouter()


@router.post("/signup", response_model=SendVerificationCodeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def signup(request: Request, user_data: SendVerificationCodeRequest, db: Session = Depends(get_db)):
    """
    Send verification code to email for signup.
    Does NOT create user yet - only sends code and stores data temporarily.

    Args:
        user_data: User registration data (email, password, first_name, last_name)

    Returns:
        SendVerificationCodeResponse with message and email

    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If error occurs
    """
    try:
        # Generate OTP and store directly in DB (safe across server restarts)
        code = ''.join(random.choices(string.digits, k=6))
        expiry = datetime.now() + timedelta(minutes=10)

        ok, err = UserModel.create_pending_user(
            db,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=user_data.password,
            code=code,
            expiry=expiry,
        )
        if not ok:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                    if "already registered" in err
                    else status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=err,
            )

        email_sent = send_verification_code_email(user_data.email, user_data.first_name, code)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending verification code. Please check your email configuration.",
            )

        return SendVerificationCodeResponse(
            message="Verification code sent to your email",
            email=user_data.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )


@router.post("/verify-signup-code", response_model=VerifyCodeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/10minutes")
async def verify_signup_code(request: Request, body: VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    Verify signup OTP (stored in DB) and activate account.
    Rate-limited: 5 attempts per 10 minutes per IP to prevent brute-force.
    """
    success, result = UserModel.verify_and_activate(db, body.email, body.code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    # Create default study background for the newly activated user
    StudyBGModel.create_default(db, result)

    return VerifyCodeResponse(
        message="Account created successfully! You can now log in."
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login and receive JWT tokens.

    Args:
        login_data: Login credentials (email, password)

    Returns:
        Token with access_token, refresh_token, and user data

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If email is not verified
    """
    # Get user by email
    user = UserModel.get_user_by_email(db, login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Block closed accounts
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been closed"
        )

    # Verify password
    if not verify_password(login_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user['id'])})
    refresh_token = create_refresh_token(data={"sub": str(user['id'])})

    # Store refresh token in database
    try:
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        sql = """
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """
        execute_query(sql, (user['id'], refresh_token, expires_at))
    except Exception as e:
        print(f"Warning: Could not store refresh token: {e}")
        # Continue anyway - token is still valid

    # Prepare user response (exclude password)
    user_response = UserResponse(**{k: v for k, v in user.items() if k != 'password'})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token

    Returns:
        New access token

    Raises:
        HTTPException 401: If refresh token is invalid or expired
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")

    # Check if refresh token exists in database and not expired
    try:
        sql = """
            SELECT * FROM refresh_tokens
            WHERE token = %s AND user_id = %s AND expires_at > NOW()
        """
        token_record = execute_query(sql, (token_data.refresh_token, user_id), fetch=True, fetch_one=True)

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking refresh token: {e}")
        # If table doesn't exist yet, skip check but log warning
        pass

    # Create new access token
    new_access_token = create_access_token(data={"sub": user_id})

    return AccessTokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(token_data: TokenRefresh):
    """
    Logout by invalidating refresh token.

    Args:
        token_data: Refresh token to invalidate

    Returns:
        Success message

    Raises:
        HTTPException 401: If token is invalid
    """
    # Verify token first
    payload = verify_token(token_data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Delete refresh token from database
    try:
        sql = "DELETE FROM refresh_tokens WHERE token = %s"
        execute_query(sql, (token_data.refresh_token,))
    except Exception as e:
        print(f"Warning: Could not delete refresh token: {e}")
        # Continue anyway

    return MessageResponse(message="Logout successful")


@router.post("/forgot-password/send-code", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password_send_code(request: Request, data: ForgotPasswordSendCodeRequest, db: Session = Depends(get_db)):
    """
    Send 6-digit reset code to email. Code stored in DB — safe across restarts.
    Rate-limited: 3 requests per minute per IP.
    """
    user = UserModel.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email has not been registered"
        )

    code = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.now() + timedelta(minutes=10)

    stored = UserModel.store_reset_code(db, user.id, code, expiry)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save verification code. Please try again."
        )

    email_sent = send_verification_code_email(data.email, user.first_name or "User", code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Please try again."
        )

    return MessageResponse(message="Verification code sent to your email")


@router.post("/forgot-password/reset", response_model=MessageResponse)
@limiter.limit("5/10minutes")
async def forgot_password_reset(request: Request, data: ForgotPasswordResetRequest, db: Session = Depends(get_db)):
    """
    Verify reset OTP (from DB) and update password.
    Rate-limited: 5 attempts per 10 minutes per IP.
    """
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    ok, result = UserModel.verify_reset_code(db, data.email, data.code)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    success, msg = UserModel.update_password(db, result, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

    return MessageResponse(message="Password reset successfully")

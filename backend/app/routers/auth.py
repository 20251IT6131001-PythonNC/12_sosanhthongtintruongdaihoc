"""
Authentication API routes.
Handles signup, login, token refresh, and logout.
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import (
    LoginRequest,
    Token,
    TokenRefresh,
    AccessTokenResponse,
    MessageResponse,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse
)
from app.schemas.user import UserResponse
from app.models.user import UserModel
from app.models.study_bg import StudyBGModel
from app.utils.security import verify_password
from app.utils.auth import create_access_token, create_refresh_token, verify_token
from app.utils.email import send_verification_code_email
from app.utils.verification import generate_verification_code, store_verification_code, verify_code, cleanup_expired_codes
from app.database import execute_query
from datetime import datetime, timedelta
from app.config import settings

router = APIRouter()


@router.post("/signup", response_model=SendVerificationCodeResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: SendVerificationCodeRequest):
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
        # Check if email already exists
        existing_user = UserModel.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Generate 6-digit code
        code = generate_verification_code()
        print(f"Generated verification code: {code} for email: {user_data.email}")

        # Store user data and code temporarily
        user_data_dict = {
            'first_name': user_data.first_name,
            'last_name': user_data.last_name,
            'email': user_data.email,
            'password': user_data.password
        }

        success = store_verification_code(user_data.email, user_data_dict, code, expiry_minutes=10)

        if not success:
            print(f"Failed to store verification code")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing signup"
            )

        print(f"Attempting to send verification email to {user_data.email}")
        # Send verification code email
        email_sent = send_verification_code_email(user_data.email, user_data.first_name, code)

        if not email_sent:
            print(f"Failed to send verification email")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending verification code. Please check your email configuration."
            )

        print(f"Verification code email sent successfully to {user_data.email}")
        return SendVerificationCodeResponse(
            message="Verification code sent to your email",
            email=user_data.email
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in signup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.post("/verify-signup-code", response_model=VerifyCodeResponse, status_code=status.HTTP_201_CREATED)
async def verify_signup_code(request: VerifyCodeRequest):
    """
    Verify signup code and create user account.

    Args:
        request: VerifyCodeRequest with email and code

    Returns:
        VerifyCodeResponse with user_id and message

    Raises:
        HTTPException 400: If code is invalid or expired
        HTTPException 500: If database error occurs
    """
    # Clean up expired codes
    cleanup_expired_codes()

    # Verify the code and get user data
    success, result = verify_code(request.email, request.code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result  # Error message
        )

    # result is now the user data dict
    user_data = result

    # Create user
    success, user_id = UserModel.create_user(
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        email=user_data['email'],
        password=user_data['password'],
        role_type=1  # Default: normal user
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating account"
        )

    # Create default study background
    StudyBGModel.create_default(user_id)

    # Mark email as verified (since they verified the code)
    UserModel.verify_email(user_id)

    return VerifyCodeResponse(
        message="Account created successfully! You can now log in.",
        user_id=user_id,
        requires_email_verification=False
    )


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
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
    user = UserModel.get_user_by_email(login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(login_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if email is verified (if verification is enabled)
    if settings.EMAIL_VERIFICATION_ENABLED:
        if not user.get('email_verified', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email first"
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

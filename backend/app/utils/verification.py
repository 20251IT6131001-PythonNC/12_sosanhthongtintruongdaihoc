"""
Temporary storage for verification codes during signup.
This stores pending signup data with verification codes.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import random
import string

# In-memory storage: {email: {code, user_data, expiry}}
_verification_codes: Dict[str, dict] = {}


def generate_verification_code() -> str:
    """Generate a random 6-digit code."""
    return ''.join(random.choices(string.digits, k=6))


def store_verification_code(email: str, user_data: dict, code: str, expiry_minutes: int = 10) -> bool:
    """
    Store verification code and user data temporarily.

    Args:
        email: User's email
        user_data: User signup data (first_name, last_name, email, password)
        code: Verification code
        expiry_minutes: Code expiry time in minutes

    Returns:
        True if stored successfully
    """
    try:
        _verification_codes[email] = {
            'code': code,
            'user_data': user_data.copy(),
            'created_at': datetime.now(),
            'expiry': datetime.now() + timedelta(minutes=expiry_minutes)
        }
        return True
    except Exception as e:
        print(f"Error storing verification code: {e}")
        return False


def get_verification_code(email: str) -> Optional[dict]:
    """
    Get stored verification code data for an email.

    Args:
        email: User's email

    Returns:
        Code data dict if found and not expired, None otherwise
    """
    if email not in _verification_codes:
        return None

    code_data = _verification_codes[email]

    # Check if expired
    if datetime.now() > code_data['expiry']:
        # Remove expired code
        del _verification_codes[email]
        return None

    return code_data


def verify_code(email: str, provided_code: str) -> Tuple[bool, str]:
    """
    Verify the provided code against stored code.

    Args:
        email: User's email
        provided_code: Code provided by user

    Returns:
        Tuple of (success: bool, message: str)
    """
    code_data = get_verification_code(email)

    if not code_data:
        return False, "Verification code not found or expired"

    if code_data['code'] != provided_code:
        return False, "Invalid verification code"

    # Get user data before clearing
    user_data = code_data['user_data']

    # Clear the code after successful verification
    del _verification_codes[email]

    return True, user_data


def clear_verification_code(email: str) -> None:
    """Clear verification code for an email."""
    if email in _verification_codes:
        del _verification_codes[email]


def cleanup_expired_codes() -> None:
    """Clean up expired verification codes."""
    now = datetime.now()
    expired_emails = [
        email for email, data in _verification_codes.items()
        if now > data['expiry']
    ]
    for email in expired_emails:
        del _verification_codes[email]

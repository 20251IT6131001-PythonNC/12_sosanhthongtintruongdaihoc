"""
User API routes.
Handles user profile retrieval, updates, and password changes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserResponse, UserUpdate, PasswordUpdate
from app.models.user import UserModel
from app.utils.security import verify_password
from app.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user's profile.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse with user details (excluding password)

    Raises:
        HTTPException 401: If not authenticated
    """
    # Remove password from response
    user_data = {k: v for k, v in current_user.items() if k != 'password'}
    return UserResponse(**user_data)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user's profile information.

    Args:
        user_update: Profile data to update
        current_user: Current authenticated user from JWT token

    Returns:
        Updated UserResponse

    Raises:
        HTTPException 400: If update data is invalid
        HTTPException 401: If not authenticated
        HTTPException 500: If database error occurs
    """
    # Prepare update data with current user values as defaults
    update_data = {
        "id": current_user['id'],
        "first_name": user_update.first_name or current_user.get("first_name"),
        "last_name": user_update.last_name or current_user.get("last_name"),
        "phone_number": user_update.phone_number or current_user.get("phone_number"),
        "country_id": user_update.country_id if user_update.country_id is not None else current_user.get("country_id"),
        "gender": user_update.gender if user_update.gender is not None else current_user.get("gender"),
        "dob": user_update.dob or current_user.get("dob"),
        "postal_code": user_update.postal_code or current_user.get("postal_code"),
        "ethnic_group": user_update.ethnic_group or current_user.get("ethnic_group"),
        "main_lang": user_update.main_lang or current_user.get("main_lang"),
        "add_lang": user_update.add_lang or current_user.get("add_lang"),
        "special": user_update.special or current_user.get("special"),
    }

    # Update user
    success, message = UserModel.update_user(update_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    # Fetch updated user from database
    updated_user = UserModel.get_user_by_id(current_user['id'])

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cannot retrieve user information after update"
        )

    # Remove password from response
    user_data = {k: v for k, v in updated_user.items() if k != 'password'}
    return UserResponse(**user_data)


@router.put("/me/password")
async def change_password(
    password_data: PasswordUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change current user's password.

    Args:
        password_data: Current and new password
        current_user: Current authenticated user from JWT token

    Returns:
        Success message

    Raises:
        HTTPException 400: If current password is incorrect
        HTTPException 401: If not authenticated
        HTTPException 500: If database error occurs
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.get('password')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password is different from current
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    success, message = UserModel.update_password(
        current_user['id'],
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    return {"message": message}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user profile by ID (admin or self only).

    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse with user details

    Raises:
        HTTPException 403: If user is not admin and not requesting own profile
        HTTPException 404: If user not found
        HTTPException 401: If not authenticated
    """
    # Check authorization: only admin or the user themselves can view
    is_admin = UserModel.is_admin(current_user.get("role_type", 1))
    if not is_admin and current_user['id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view other user information"
        )

    # Get user
    user = UserModel.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Remove password from response
    user_data = {k: v for k, v in user.items() if k != 'password'}
    return UserResponse(**user_data)

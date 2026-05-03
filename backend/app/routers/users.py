"""
User API routes.
Handles user profile retrieval, updates, and password changes.
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserUpdate, PasswordUpdate, CloseAccountRequest, AdminUserCreate, AdminUserUpdate
from app.models.user import UserModel
from app.utils.security import verify_password
from app.dependencies import get_current_user
from app.database import get_db
from typing import Dict, Any, List
import os
import uuid
import shutil

AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

router = APIRouter()


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    limit: int = 1000,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all users (admin only).
    """
    if not UserModel.is_admin(current_user.get("role_type", 1)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    users, _ = UserModel.get_all_users(db, page=1, limit=limit)
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    payload: AdminUserCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user account (admin only)."""
    if not UserModel.is_admin(current_user.get("role_type", 1)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    existing = UserModel.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    success, user_id = UserModel.create_user(
        db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password=payload.password,
        role_type=payload.role_type,
        email_verified=True,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    # Update optional fields
    extra = payload.model_dump(exclude={"first_name", "last_name", "email", "password", "role_type"})
    extra_data = {k: v for k, v in extra.items() if v is not None}
    if extra_data:
        extra_data["id"] = user_id
        extra_data["first_name"] = payload.first_name
        extra_data["last_name"] = payload.last_name
        extra_data["email"] = payload.email
        UserModel.update_user(db, extra_data)

    user = UserModel.get_user_by_id(db, user_id)
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update any user account (admin only)."""
    if not UserModel.is_admin(current_user.get("role_type", 1)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    user = UserModel.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = payload.model_dump(exclude_none=True)

    # Handle password separately
    if "password" in updates:
        UserModel.update_password(db, user_id, updates.pop("password"))

    # Handle role_type separately (update_user doesn't support it)
    if "role_type" in updates:
        from app.entities.user import User as UserEntity
        db.query(UserEntity).filter(UserEntity.id == user_id).update({UserEntity.role_type: updates.pop("role_type")})
        db.commit()

    # Handle image separately
    if "image" in updates:
        from app.entities.user import User as UserEntity
        db.query(UserEntity).filter(UserEntity.id == user_id).update({UserEntity.image: updates.pop("image")})
        db.commit()

    if updates:
        update_data = {
            "id": user_id,
            "first_name": updates.get("first_name", user["first_name"]),
            "last_name": updates.get("last_name", user["last_name"]),
            "email": updates.get("email", user["email"]),
            **{k: v for k, v in updates.items() if k not in ("first_name", "last_name", "email")},
        }
        UserModel.update_user(db, update_data)

    updated = UserModel.get_user_by_id(db, user_id)
    return updated.to_dict()


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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        "email": current_user.get("email"),
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
    success, message = UserModel.update_user(db, update_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    # Fetch updated user from database
    updated_user = UserModel.get_user_by_id(db, current_user['id'])

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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        db,
        current_user['id'],
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    return {"message": message}


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a new avatar image for the current user."""
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")

    # Limit file size: 5 MB
    contents = await file.read(5 * 1024 * 1024 + 1)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image must be under 5 MB")

    ext = os.path.splitext(file.filename or "avatar")[1] or ".jpg"
    filename = f"{current_user['id']}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    image_url = f"/static/avatars/{filename}"

    # Remove old avatar file if it exists and is local
    old_image = current_user.get("image") or ""
    if old_image.startswith("/static/avatars/"):
        old_path = os.path.join(AVATAR_DIR, os.path.basename(old_image))
        if os.path.exists(old_path):
            os.remove(old_path)

    from app.entities.user import User as UserEntity
    db.query(UserEntity).filter(UserEntity.id == current_user["id"]).update({UserEntity.image: image_url})
    db.commit()

    updated = UserModel.get_user_by_id(db, current_user["id"])
    return updated.to_dict()


@router.post("/me/close", status_code=status.HTTP_200_OK)
async def close_account(
    request: CloseAccountRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Close (deactivate) current user's account.
    Verifies password then sets is_active=False and stores the reason.
    """
    user = UserModel.get_user_by_id(db, current_user['id'])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(request.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    success, msg = UserModel.close_account(db, current_user['id'], request.reason)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

    return {"message": msg}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    user = UserModel.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Remove password from response
    user_data = {k: v for k, v in user.items() if k != 'password'}
    return UserResponse(**user_data)

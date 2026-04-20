"""
Study Background API routes.
Handles user study background information (academic records, test scores).
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.study_bg import StudyBGResponse, StudyBGUpdate
from app.models.study_bg import StudyBGModel
from app.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.get("/me", response_model=StudyBGResponse)
async def get_current_user_study_bg(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user's study background.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        StudyBGResponse with user's study background

    Raises:
        HTTPException 404: If study background not found
        HTTPException 401: If not authenticated
    """
    study_bg = StudyBGModel.get_by_user_id(current_user['id'])

    if not study_bg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có dữ liệu học tập"
        )

    return StudyBGResponse(**study_bg)


@router.post("/me", response_model=StudyBGResponse)
async def create_study_bg(
    study_bg_data: StudyBGUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create or replace study background for current user.

    Args:
        study_bg_data: Study background information
        current_user: Current authenticated user from JWT token

    Returns:
        StudyBGResponse with created study background

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 500: If database error occurs
    """
    # First, delete existing if any
    StudyBGModel.delete(current_user['id'])

    # Create new one with provided data
    data = {
        'level': study_bg_data.level,
        'major': study_bg_data.major,
        'academic_rate': study_bg_data.academic_rate,
        'gpa': study_bg_data.gpa,
        'graduate_year': study_bg_data.graduate_year,
        'act': study_bg_data.act,
        'gmat': study_bg_data.gmat,
        'sat': study_bg_data.sat,
        'cat': study_bg_data.cat,
        'gre': study_bg_data.gre,
        'stat': study_bg_data.stat,
        'ielts': study_bg_data.ielts,
        'toefl': study_bg_data.toefl,
        'pearson_test': study_bg_data.pearson_test,
        'cam_adv_test': study_bg_data.cam_adv_test,
        'inter_bac': study_bg_data.inter_bac,
    }

    success, message = StudyBGModel.update(current_user['id'], data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    # Fetch the created record
    study_bg = StudyBGModel.get_by_user_id(current_user['id'])

    if not study_bg:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy dữ liệu sau khi tạo"
        )

    return StudyBGResponse(**study_bg)


@router.put("/me", response_model=StudyBGResponse)
async def update_study_bg(
    study_bg_data: StudyBGUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user's study background.

    Args:
        study_bg_data: Fields to update (all optional)
        current_user: Current authenticated user from JWT token

    Returns:
        Updated StudyBGResponse

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 500: If database error occurs
    """
    # Get current study background
    existing_bg = StudyBGModel.get_by_user_id(current_user['id'])

    if not existing_bg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có dữ liệu học tập"
        )

    # Prepare update data - only update provided fields
    update_data = {}
    for field in ['level', 'major', 'academic_rate', 'gpa', 'graduate_year',
                  'act', 'gmat', 'sat', 'cat', 'gre', 'stat',
                  'ielts', 'toefl', 'pearson_test', 'cam_adv_test', 'inter_bac']:
        value = getattr(study_bg_data, field, None)
        if value is not None:
            update_data[field] = value
        else:
            # Keep existing value
            update_data[field] = existing_bg.get(field)

    # Update
    success, message = StudyBGModel.update(current_user['id'], update_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    # Fetch updated record
    updated_bg = StudyBGModel.get_by_user_id(current_user['id'])

    if not updated_bg:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy dữ liệu sau khi cập nhật"
        )

    return StudyBGResponse(**updated_bg)


@router.delete("/me")
async def delete_study_bg(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete current user's study background.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        Success message

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 500: If database error occurs
    """
    success = StudyBGModel.delete(current_user['id'])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa dữ liệu học tập"
        )

    return {"message": "Xóa dữ liệu học tập thành công"}


@router.get("/{user_id}", response_model=StudyBGResponse)
async def get_user_study_bg(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get study background for a specific user (admin or self only).

    Args:
        user_id: ID of user whose study background to retrieve
        current_user: Current authenticated user from JWT token

    Returns:
        StudyBGResponse

    Raises:
        HTTPException 403: If not admin and not requesting own data
        HTTPException 404: If study background not found
        HTTPException 401: If not authenticated
    """
    from app.models.user import UserModel

    # Check authorization: only admin or the user themselves
    is_admin = UserModel.is_admin(current_user.get("role_type", 1))
    if not is_admin and current_user['id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem dữ liệu này"
        )

    study_bg = StudyBGModel.get_by_user_id(user_id)

    if not study_bg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có dữ liệu học tập cho người dùng này"
        )

    return StudyBGResponse(**study_bg)

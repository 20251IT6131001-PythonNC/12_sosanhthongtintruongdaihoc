"""
Pydantic schemas for User-related requests and responses.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    country_id: Optional[int] = None
    gender: Optional[bool] = None  # True = Male, False = Female (based on DB)
    dob: Optional[date] = None
    postal_code: Optional[str] = None
    ethnic_group: Optional[str] = None
    main_lang: Optional[str] = None
    add_lang: Optional[str] = None
    special: Optional[str] = None


class PasswordUpdate(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    country_id: Optional[int] = None
    gender: Optional[bool] = None
    dob: Optional[date] = None
    postal_code: Optional[str] = None
    ethnic_group: Optional[str] = None
    main_lang: Optional[str] = None
    add_lang: Optional[str] = None
    special: Optional[str] = None
    role_type: int  # 1 = user, 2 = admin
    insert_date: Optional[datetime] = None
    update_date: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows creating from ORM models

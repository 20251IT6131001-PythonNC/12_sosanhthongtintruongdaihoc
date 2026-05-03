"""
Pydantic schemas for Country-related requests and responses.
"""
from pydantic import BaseModel
from typing import Optional


class CountryBase(BaseModel):
    """Base country schema"""
    name: str


class CountryResponse(CountryBase):
    """Schema for country in response"""
    id: int
    region_id: Optional[int] = None
    region: Optional[str] = None

    class Config:
        from_attributes = True

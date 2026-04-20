"""
Pydantic schemas for Country-related requests and responses.
"""
from pydantic import BaseModel


class CountryBase(BaseModel):
    """Base country schema"""
    name: str


class CountryResponse(CountryBase):
    """Schema for country in response"""
    id: int

    class Config:
        from_attributes = True

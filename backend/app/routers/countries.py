"""
Country API routes.
Handles country listing and searching.
"""
from fastapi import APIRouter, HTTPException, status, Query, Path, Depends
from sqlalchemy.orm import Session
from app.schemas.country import CountryResponse
from app.models.country import CountryModel
from app.database import get_db
from typing import List

router = APIRouter()


@router.get("", response_model=List[CountryResponse])
async def list_countries(db: Session = Depends(get_db)):
    """
    Get list of all countries.

    Returns:
        List of all CountryResponse sorted by name
    """
    countries = CountryModel.get_all(db)

    if not countries:
        return []

    return countries


@router.get("/search", response_model=List[CountryResponse])
async def search_countries(
    q: str = Query(..., min_length=1, description="Country name to search"),
    db: Session = Depends(get_db),
):
    """
    Search countries by name (partial match).

    Args:
        q: Country name or part of it

    Returns:
        List of matching CountryResponse

    Raises:
        HTTPException 400: If search query is empty
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên quốc gia không được để trống"
        )

    countries = CountryModel.search_by_name(db, q.strip())
    return countries


@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: int = Path(..., gt=0, description="Country ID"),
    db: Session = Depends(get_db),
):
    """
    Get country by ID.

    Args:
        country_id: ID of the country

    Returns:
        CountryResponse

    Raises:
        HTTPException 404: If country not found
    """
    country = CountryModel.get_by_id(db, country_id)

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy quốc gia"
        )

    return country


@router.get("/by-region/{region_id}", response_model=List[CountryResponse])
async def get_countries_by_region(
    region_id: int = Path(..., gt=0, description="Region ID (1-6)"),
    db: Session = Depends(get_db),
):
    """
    Get all countries belonging to a region.

    Args:
        region_id: 1=Asia, 2=Europe, 3=North America, 4=Latin America, 5=Oceania, 6=Africa

    Returns:
        List of CountryResponse
    """
    return CountryModel.get_by_region_id(db, region_id)

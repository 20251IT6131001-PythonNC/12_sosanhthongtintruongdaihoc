"""
University API routes.
Handles university listing, search, filtering, and comparison.
"""
from fastapi import APIRouter, HTTPException, status, Query, Path
from app.schemas.university import (
    UniversityListResponse,
    UniversityDetailResponse,
    UniversityCompareRequest,
    EntryRequirementsResponse,
    ChartDataResponse,
    DetailInformation
)
from app.models.university import UniversityModel
from typing import List

router = APIRouter()


@router.get("/", response_model=List[UniversityListResponse])
async def list_universities(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of universities to return")
):
    """
    Get list of all universities with their basic information and scores.

    Args:
        limit: Maximum number of results (default: 50, max: 200)

    Returns:
        List of UniversityListResponse
    """
    universities = UniversityModel.get_all_universities(limit=limit)

    if not universities:
        return []

    return universities


@router.get("/search", response_model=List[UniversityListResponse])
async def search_universities(
    q: str = Query(..., min_length=1, description="University name to search")
):
    """
    Search universities by name (partial match).

    Args:
        q: University name or part of it

    Returns:
        List of matching UniversityListResponse

    Raises:
        HTTPException 400: If search query is empty
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    universities = UniversityModel.search_universities_by_name(q.strip())
    return universities


@router.get("/filter", response_model=List[UniversityListResponse])
async def filter_universities(
    region: str = Query(None, description="Filter by region"),
    country: str = Query(None, description="Filter by country"),
    min_rank: int = Query(None, ge=1, description="Minimum ranking"),
    max_rank: int = Query(None, ge=1, description="Maximum ranking")
):
    """
    Filter universities by region, country, and ranking.

    Args:
        region: Region filter (optional)
        country: Country filter (optional)
        min_rank: Minimum ranking (optional)
        max_rank: Maximum ranking (optional)

    Returns:
        List of filtered UniversityListResponse
    """
    universities = UniversityModel.filter_universities(
        region=region,
        country=country,
        min_rank=min_rank,
        max_rank=max_rank
    )
    return universities


@router.get("/{university_id}", response_model=UniversityDetailResponse)
async def get_university_detail(
    university_id: int = Path(..., gt=0, description="University ID")
):
    """
    Get detailed information about a specific university.

    Args:
        university_id: ID of the university

    Returns:
        UniversityDetailResponse with complete information

    Raises:
        HTTPException 404: If university not found
    """
    university = UniversityModel.get_university_by_id(university_id)

    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

    # Get detail information
    detail_info = UniversityModel.get_detail_information(university_id)

    if detail_info:
        university['detail_info'] = detail_info

    return university


@router.get("/{university_id}/entry-requirements", response_model=EntryRequirementsResponse)
async def get_entry_requirements(
    university_id: int = Path(..., gt=0, description="University ID"),
    degree_type: int = Query(1, ge=1, le=2, description="1 for bachelor, 2 for master")
):
    """
    Get entry requirements for a specific university and degree type.

    Args:
        university_id: ID of the university
        degree_type: 1 for bachelor (default), 2 for master

    Returns:
        EntryRequirementsResponse with entry exam scores

    Raises:
        HTTPException 404: If university not found
    """
    requirements = UniversityModel.get_entry_requirements(university_id, degree_type)

    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entry requirements found"
        )

    return requirements


@router.post("/compare", response_model=List[DetailInformation])
async def compare_universities(
    compare_request: UniversityCompareRequest
):
    """
    Compare multiple universities side-by-side.

    Args:
        compare_request: List of university IDs to compare

    Returns:
        List of DetailInformation for each university

    Raises:
        HTTPException 400: If no universities provided
        HTTPException 404: If no matching universities found
    """
    if not compare_request.university_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one university to compare"
        )

    comparison_data = UniversityModel.get_comparison_data(compare_request.university_ids)

    if not comparison_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comparison data found"
        )

    # Convert to DetailInformation response
    result = []
    for data in comparison_data:
        detail_info = DetailInformation(
            fee=data.get('fee'),
            scholarship=bool(data.get('scholarship')),
            domestic=data.get('domestic'),
            international=data.get('international'),
            total_stu=data.get('total_stu'),
            ug_rate=data.get('ug_rate'),
            pg_rate=data.get('pg_rate'),
            inter_total=data.get('inter_total'),
            inter_ug_rate=data.get('inter_ug_rate'),
            inter_pg_rate=data.get('inter_pg_rate')
        )
        result.append(detail_info)

    return result


@router.post("/chart-data", response_model=List[ChartDataResponse])
async def get_chart_data(
    compare_request: UniversityCompareRequest
):
    """
    Get chart data for entry requirements comparison.

    Args:
        compare_request: List of university IDs

    Returns:
        List of ChartDataResponse for chart visualization

    Raises:
        HTTPException 400: If no universities provided
    """
    if not compare_request.university_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one university"
        )

    chart_data = UniversityModel.get_chart_data(compare_request.university_ids)
    return chart_data


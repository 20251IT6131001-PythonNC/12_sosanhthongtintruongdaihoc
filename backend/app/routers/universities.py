"""
University API routes.
Handles university listing, search, filtering, and comparison.
"""
from fastapi import APIRouter, HTTPException, status, Query, Path, Depends
from sqlalchemy.orm import Session
from app.schemas.university import (
    UniversityListResponse,
    UniversityDetailResponse,
    UniversityCompareRequest,
    EntryRequirementsResponse,
    ChartDataResponse,
    DetailInformation,
    UniversityCreateRequest,
    UniversityCreateResponse,
)
from app.models.university import UniversityModel
from app.database import get_db
from typing import List, Optional

router = APIRouter()


@router.get("/regions", response_model=List[dict])
async def list_regions(db: Session = Depends(get_db)):
    """Get all distinct regions as {id, name} list."""
    return UniversityModel.get_regions(db)


@router.get("/countries-by-region", response_model=List[dict])
async def list_countries_by_region(
    region_id: int = Query(None, description="Filter countries by region ID"),
    db: Session = Depends(get_db),
):
    """Get countries, optionally filtered by region_id."""
    return UniversityModel.get_countries_by_region(db, region_id=region_id)


@router.get("", response_model=List[UniversityListResponse])
async def list_universities(
    limit: int = Query(50, ge=1, le=2000, description="Maximum number of universities to return"),
    db: Session = Depends(get_db),
):
    """
    Get list of all universities with their basic information and scores.

    Args:
        limit: Maximum number of results (default: 50, max: 200)

    Returns:
        List of UniversityListResponse
    """
    universities = UniversityModel.get_all_universities(db, limit=limit)

    if not universities:
        return []

    return universities


@router.get("/search", response_model=List[UniversityListResponse])
async def search_universities(
    q: str = Query(..., min_length=1, description="University name to search"),
    db: Session = Depends(get_db),
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

    universities = UniversityModel.search_universities_by_name(db, q.strip())
    return universities


@router.get("/filter", response_model=List[UniversityListResponse])
async def filter_universities(
    region_id: int = Query(None, description="Filter by region ID"),
    country: str = Query(None, description="Filter by country"),
    city: str = Query(None, description="Filter by city"),
    min_rank: int = Query(None, ge=1, description="Minimum ranking"),
    max_rank: int = Query(None, ge=1, description="Maximum ranking"),
    english_tests: Optional[List[str]] = Query(None, description="English test requirements (IELTS, TOEFL, ...)"),
    academic_tests: Optional[List[str]] = Query(None, description="Academic test requirements (SAT, GRE, ...)"),
    min_international_pct: Optional[float] = Query(None, ge=0, le=100, description="Minimum international student percentage"),
    db: Session = Depends(get_db),
):
    universities = UniversityModel.filter_universities(
        db,
        region_id=region_id,
        country=country,
        city=city,
        min_rank=min_rank,
        max_rank=max_rank,
        english_tests=english_tests,
        academic_tests=academic_tests,
        min_international_pct=min_international_pct,
    )
    return universities


@router.get("/{university_id}/ranking-scores")
async def get_university_ranking_scores(
    university_id: int = Path(..., gt=0, description="University ID"),
    db: Session = Depends(get_db),
):
    """Return per-indicator score and rank_int grouped by score_type category."""
    return UniversityModel.get_ranking_scores(db, university_id)


@router.get("/{university_id}", response_model=UniversityDetailResponse)
async def get_university_detail(
    university_id: int = Path(..., gt=0, description="University ID"),
    db: Session = Depends(get_db),
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
    university = UniversityModel.get_university_by_id(db, university_id)

    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

    # Get detail information
    detail_info = UniversityModel.get_detail_information(db, university_id)
    if detail_info:
        university['detail_info'] = detail_info

    # Get entry requirements + scores for edit form
    edit_data = UniversityModel.get_edit_data(db, university_id)
    university['entry_requirements'] = edit_data['entry_requirements']
    university['edit_scores'] = edit_data['edit_scores']

    # Get scholarships from scholarships table
    university['scholarships'] = UniversityModel.get_scholarships(db, university_id)

    return university


@router.get("/{university_id}/entry-requirements", response_model=EntryRequirementsResponse)
async def get_entry_requirements(
    university_id: int = Path(..., gt=0, description="University ID"),
    degree_type: int = Query(1, ge=1, le=2, description="1 for bachelor, 2 for master"),
    db: Session = Depends(get_db),
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
    requirements = UniversityModel.get_entry_requirements(db, university_id, degree_type)

    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entry requirements found"
        )

    return requirements


@router.post("/compare", response_model=List[DetailInformation])
async def compare_universities(
    compare_request: UniversityCompareRequest,
    db: Session = Depends(get_db),
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

    comparison_data = UniversityModel.get_comparison_data(db, compare_request.university_ids)

    if not comparison_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No comparison data found"
        )

    # Convert to DetailInformation response
    result = []
    for data in comparison_data:
        detail_info = DetailInformation(
            id=data.get('id'),
            name=data.get('name'),
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
    compare_request: UniversityCompareRequest,
    db: Session = Depends(get_db),
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

    chart_data = UniversityModel.get_chart_data(db, compare_request.university_ids)
    return chart_data


@router.post("", response_model=UniversityCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_university(
    payload: UniversityCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new university with detail info, entry requirements, and scores."""
    result = UniversityModel.create_university(db, payload.model_dump())
    return result


@router.put("/{university_id}", response_model=UniversityCreateResponse)
async def update_university(
    university_id: int = Path(..., gt=0),
    payload: UniversityCreateRequest = ...,
    db: Session = Depends(get_db),
):
    """Update an existing university."""
    result = UniversityModel.update_university(db, university_id, payload.model_dump())
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")
    return result


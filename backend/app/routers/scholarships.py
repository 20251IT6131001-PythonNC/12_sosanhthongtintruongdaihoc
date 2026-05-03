"""
Scholarships API routes.
Returns scholarships with associated university info (name, logo).
"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.entities.scholarship import Scholarship
from app.entities.university import University

router = APIRouter()


@router.get("", response_model=List[dict])
async def list_scholarships(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Return all scholarships joined with university name and logo.
    """
    rows = (
        db.query(Scholarship)
        .options(joinedload(Scholarship.university))
        .limit(limit)
        .all()
    )

    result = []
    for s in rows:
        uni: Optional[University] = s.university
        result.append({
            "id": s.id,
            "name": s.name,
            "value": s.value,
            "duration": s.duration,
            "criteria": s.criteria,
            "university_id": s.university_id,
            "university_name": uni.name if uni else None,
            "university_logo": uni.logo if uni else None,
        })
    return result

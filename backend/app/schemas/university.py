"""
Pydantic schemas for University-related requests and responses.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ScholarshipItem(BaseModel):
    """Schema for a single scholarship entry"""
    id: Optional[int] = None
    name: str = ""
    value: Optional[float] = None
    duration: Optional[str] = None
    criteria: Optional[str] = None


class ScoreDetail(BaseModel):
    """Schema for individual indicator score"""
    indicator_id: str
    indicator_name: str
    rank: Optional[str] = None
    score: Optional[str] = None


class UniversityScores(BaseModel):
    """Schema for university scores by category"""
    research_discovery: Optional[Dict[str, Optional[float]]] = None
    learning_experience: Optional[Dict[str, Optional[float]]] = None
    employability: Optional[Dict[str, Optional[float]]] = None
    global_engagement: Optional[Dict[str, Optional[float]]] = None
    sustainability: Optional[Dict[str, Optional[float]]] = None


class EntryRequirementByDegree(BaseModel):
    """Schema for entry requirements by degree type"""
    sat: Optional[str] = None
    gre: Optional[str] = None
    gmat: Optional[str] = None
    act: Optional[str] = None
    atar: Optional[str] = None
    gpa: Optional[str] = None
    toefl: Optional[str] = None
    ielts: Optional[str] = None


class DetailInformation(BaseModel):
    """Schema for university detail information"""
    id: Optional[int] = None
    name: Optional[str] = None
    fee: Optional[str] = None
    scholarship: Optional[bool] = None
    domestic: Optional[str] = None
    international: Optional[str] = None
    english_test: Optional[str] = None
    academic_test: Optional[str] = None
    total_stu: Optional[str] = None
    ug_rate: Optional[str] = None
    pg_rate: Optional[str] = None
    inter_total: Optional[str] = None
    inter_ug_rate: Optional[str] = None
    inter_pg_rate: Optional[str] = None


class UniversityBase(BaseModel):
    """Base university schema"""
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    country_id: Optional[int] = None
    region_id: Optional[int] = None
    logo: Optional[str] = None
    overall_score: Optional[float] = None
    rank_int: Optional[int] = None


class UniversityResponse(UniversityBase):
    """Schema for university in response"""
    id: int
    path: Optional[str] = None
    scores: Optional[Dict[str, Dict[str, Optional[float]]]] = None

    class Config:
        from_attributes = True


class UniversityDetailResponse(UniversityResponse):
    """Extended university response with detail information"""
    detail_info: Optional[DetailInformation] = None
    entry_requirements: Optional[List[Any]] = None
    edit_scores: Optional[Dict[str, Any]] = None
    scholarships: Optional[List[ScholarshipItem]] = None


class UniversityListResponse(BaseModel):
    """Schema for paginated university list response"""
    id: int
    rank: Optional[int] = None
    overall_score: Optional[float] = None
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None
    scores: Optional[Dict[str, Dict[str, Optional[float]]]] = None


class UniversityFilter(BaseModel):
    """Schema for filtering universities"""
    region_id: Optional[int] = None
    country: Optional[str] = None
    ranking: Optional[tuple[int, int]] = None


class UniversityCompareRequest(BaseModel):
    """Schema for comparing multiple universities"""
    university_ids: List[int]


class EntryRequirementsResponse(BaseModel):
    """Schema for entry requirements response"""
    name: str
    address: Optional[str] = None
    rank: Optional[int] = None
    bachelor: Optional[EntryRequirementByDegree] = None
    master: Optional[EntryRequirementByDegree] = None


class ChartEntryData(BaseModel):
    """Schema for entry scores in one degree type"""
    sat: Optional[float] = None
    gre: Optional[float] = None
    gmat: Optional[float] = None
    act: Optional[float] = None
    atar: Optional[float] = None
    gpa: Optional[float] = None
    toefl: Optional[float] = None
    ielts: Optional[float] = None


class ChartDataResponse(BaseModel):
    """Schema for chart data response (both degree types)"""
    id: Optional[int] = None
    name: str
    bachelor: Optional[ChartEntryData] = None
    master: Optional[ChartEntryData] = None


# ── Create / Update ──────────────────────────────────────────────────────────

class EntryInforCreate(BaseModel):
    SAT:  Optional[str] = None
    ACT:  Optional[str] = None
    GRE:  Optional[str] = None
    GMAT: Optional[str] = None
    ATAR: Optional[str] = None
    GPA:  Optional[str] = None
    TOEFL: Optional[str] = None
    IELTS: Optional[str] = None


class DetailInforCreate(BaseModel):
    fee:           Optional[str] = None
    scholarship:   Optional[bool] = None
    domestic:      Optional[str] = None
    international: Optional[str] = None
    english_test:  Optional[str] = None
    academic_test: Optional[str] = None
    total_stu:     Optional[str] = None
    ug_rate:       Optional[str] = None
    pg_rate:       Optional[str] = None
    inter_total:   Optional[str] = None
    inter_ug_rate: Optional[str] = None
    inter_pg_rate: Optional[str] = None


class IndicatorScoreCreate(BaseModel):
    score: Optional[float] = None
    rank:  Optional[int] = None


class UniversityCreateRequest(BaseModel):
    name:          str
    city:          Optional[str] = None
    country_id:    Optional[int] = None
    logo:          Optional[str] = None
    path:          Optional[str] = None
    rank_int:      Optional[int] = None
    overall_score: Optional[float] = None
    detail:        Optional[DetailInforCreate] = None
    # key = degree_type as string ("1" or "2")
    entry:         Optional[Dict[str, EntryInforCreate]] = None
    # key = indicator_key (e.g. "academic_reputation"), value = score+rank
    scores:        Optional[Dict[str, IndicatorScoreCreate]] = None


class UniversityCreateResponse(BaseModel):
    id: int
    name: str

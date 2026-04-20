"""
Pydantic schemas for University-related requests and responses.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


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
    region: Optional[str] = None
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
    region: Optional[str] = None
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


class ChartDataResponse(BaseModel):
    """Schema for chart data response"""
    name: str
    sat: Optional[float] = None
    gre: Optional[float] = None
    gmat: Optional[float] = None
    act: Optional[float] = None
    atar: Optional[float] = None
    gpa: Optional[float] = None
    toefl: Optional[float] = None
    ielts: Optional[float] = None

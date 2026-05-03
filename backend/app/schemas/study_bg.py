"""
Pydantic schemas for Study Background-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional


class StudyBGBase(BaseModel):
    """Base study background schema"""
    level: Optional[str] = None
    major: Optional[str] = None
    academic_rate: Optional[float] = Field(None, ge=0, le=4)
    gpa: Optional[float] = Field(None, ge=0, le=4)
    graduate_year: Optional[int] = Field(None, ge=1900, le=2100)


class TestScoresBase(BaseModel):
    """Academic test scores"""
    act: Optional[int] = Field(None, ge=1, le=36)
    gmat: Optional[int] = Field(None, ge=200, le=800)
    sat: Optional[int] = Field(None, ge=400, le=1600)
    cat: Optional[int] = None
    gre: Optional[int] = Field(None, ge=260, le=340)
    stat: Optional[int] = None


class LanguageTestsBase(BaseModel):
    """Language proficiency tests"""
    ielts: Optional[float] = Field(None, ge=0, le=9)
    toefl: Optional[int] = Field(None, ge=0, le=120)
    pearson_test: Optional[int] = Field(None, ge=10, le=90)
    cam_adv_test: Optional[int] = Field(None, ge=0, le=230)
    inter_bac: Optional[float] = Field(None, ge=0, le=45)


class StudyBGCreate(StudyBGBase, TestScoresBase, LanguageTestsBase):
    """Schema for creating study background"""
    pass


class StudyBGUpdate(BaseModel):
    """Schema for updating study background"""
    level: Optional[str] = None
    major: Optional[str] = None
    academic_rate: Optional[float] = Field(None, ge=0, le=4)
    gpa: Optional[float] = Field(None, ge=0, le=4)
    graduate_year: Optional[int] = Field(None, ge=1900, le=2100)
    act: Optional[int] = Field(None, ge=1, le=36)
    gmat: Optional[int] = Field(None, ge=200, le=800)
    sat: Optional[int] = Field(None, ge=400, le=1600)
    cat: Optional[int] = None
    gre: Optional[int] = Field(None, ge=260, le=340)
    stat: Optional[int] = None
    ielts: Optional[float] = Field(None, ge=0, le=9)
    toefl: Optional[int] = Field(None, ge=0, le=120)
    pearson_test: Optional[int] = Field(None, ge=10, le=90)
    cam_adv_test: Optional[int] = Field(None, ge=0, le=230)
    inter_bac: Optional[float] = Field(None, ge=0, le=45)


class StudyBGResponse(StudyBGBase, TestScoresBase, LanguageTestsBase):
    """Schema for study background in response"""
    id: Optional[int] = None
    user_id: int

    class Config:
        from_attributes = True

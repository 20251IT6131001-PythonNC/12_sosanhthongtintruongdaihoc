"""
Entity: DetailInfor
SQLAlchemy ORM model for the `detail_infors` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from app.database import Base

if TYPE_CHECKING:
    from .university import University


class DetailInfor(Base):
    __tablename__ = "detail_infors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id"), nullable=True
    )
    fee: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scholarship: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    domestic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    international: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    english_test: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    academic_test: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_stu: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ug_rate: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    pg_rate: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    inter_total: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    inter_ug_rate: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    inter_pg_rate: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # N DetailInfor  →  1 University  (n-1 / 1-1 từ phía University, FK: university_id)
    university: Mapped[Optional["University"]] = relationship(
        "University", back_populates="detail_infor"
    )

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "DetailInfor":
        obj = cls()
        obj.id = data.get("id")
        obj.university_id = data.get("university_id")
        obj.fee = data.get("fee")
        obj.scholarship = data.get("scholarship")
        obj.domestic = data.get("domestic")
        obj.international = data.get("international")
        obj.english_test = data.get("english_test")
        obj.academic_test = data.get("academic_test")
        obj.total_stu = data.get("total_stu")
        obj.ug_rate = data.get("ug_rate")
        obj.pg_rate = data.get("pg_rate")
        obj.inter_total = data.get("inter_total")
        obj.inter_ug_rate = data.get("inter_ug_rate")
        obj.inter_pg_rate = data.get("inter_pg_rate")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "university_id": self.university_id,
            "fee": self.fee,
            "scholarship": self.scholarship,
            "domestic": self.domestic,
            "international": self.international,
            "english_test": self.english_test,
            "academic_test": self.academic_test,
            "total_stu": self.total_stu,
            "ug_rate": self.ug_rate,
            "pg_rate": self.pg_rate,
            "inter_total": self.inter_total,
            "inter_ug_rate": self.inter_ug_rate,
            "inter_pg_rate": self.inter_pg_rate,
        }

    def __repr__(self) -> str:
        return f"<DetailInfor id={self.id} uni={self.university_id}>"

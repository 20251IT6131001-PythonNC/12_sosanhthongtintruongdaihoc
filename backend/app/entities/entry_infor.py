"""
Entity: EntryInfor
SQLAlchemy ORM model for the `entry_infor` table.
DB columns SAT/GRE/GMAT/ACT/ATAR/GPA/TOEFL/IELTS are uppercase in MySQL.
"""
from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Dict, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .university import University


class EntryInfor(Base):
    __tablename__ = "entry_infor"

    DEGREE_BACHELOR = 1
    DEGREE_MASTER = 2
    DEGREE_LABELS = {
        1: "Bachelor's Degree",
        2: "Master's Degree",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id"), nullable=True
    )
    degree_type: Mapped[int] = mapped_column(Integer, default=1)
    # DB column names are uppercase; Python attrs are lowercase
    sat: Mapped[Optional[str]] = mapped_column("SAT", String(100), nullable=True)
    gre: Mapped[Optional[str]] = mapped_column("GRE", String(100), nullable=True)
    gmat: Mapped[Optional[str]] = mapped_column("GMAT", String(100), nullable=True)
    act: Mapped[Optional[str]] = mapped_column("ACT", String(100), nullable=True)
    atar: Mapped[Optional[str]] = mapped_column("ATAR", String(100), nullable=True)
    gpa: Mapped[Optional[str]] = mapped_column("GPA", String(100), nullable=True)
    toefl: Mapped[Optional[str]] = mapped_column("TOEFL", String(100), nullable=True)
    ielts: Mapped[Optional[str]] = mapped_column("IELTS", String(100), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # N EntryInfor  →  1 University  (n-1, FK: university_id)
    university: Mapped[Optional["University"]] = relationship(
        "University", back_populates="entry_infors"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_degree_label(self) -> str:
        return self.DEGREE_LABELS.get(self.degree_type, "Unknown")

    def get_test_requirements(self) -> Dict[str, Optional[str]]:
        return {
            "SAT": self.sat,
            "GRE": self.gre,
            "GMAT": self.gmat,
            "ACT": self.act,
            "ATAR": self.atar,
            "GPA": self.gpa,
            "TOEFL": self.toefl,
            "IELTS": self.ielts,
        }

    def get_required_tests(self) -> List[str]:
        return [k for k, v in self.get_test_requirements().items() if v is not None]

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "EntryInfor":
        obj = cls()
        obj.id = data.get("id")
        obj.university_id = data.get("university_id")
        obj.degree_type = data.get("degree_type", 1)
        obj.sat = data.get("sat") or data.get("SAT")
        obj.gre = data.get("gre") or data.get("GRE")
        obj.gmat = data.get("gmat") or data.get("GMAT")
        obj.act = data.get("act") or data.get("ACT")
        obj.atar = data.get("atar") or data.get("ATAR")
        obj.gpa = data.get("gpa") or data.get("GPA")
        obj.toefl = data.get("toefl") or data.get("TOEFL")
        obj.ielts = data.get("ielts") or data.get("IELTS")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "university_id": self.university_id,
            "degree_type": self.degree_type,
            "degree_label": self.get_degree_label(),
            "SAT": self.sat,
            "GRE": self.gre,
            "GMAT": self.gmat,
            "ACT": self.act,
            "ATAR": self.atar,
            "GPA": self.gpa,
            "TOEFL": self.toefl,
            "IELTS": self.ielts,
        }

    def __repr__(self) -> str:
        return (
            f"<EntryInfor id={self.id} uni={self.university_id} "
            f"degree={self.get_degree_label()}>"
        )

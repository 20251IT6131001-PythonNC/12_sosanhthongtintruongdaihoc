"""
Entity: StudyBackground
SQLAlchemy ORM model for the `study_bg` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from app.database import Base

if TYPE_CHECKING:
    from .user import User


class StudyBackground(Base):
    __tablename__ = "study_bg"

    # Academic tests with their score ranges for validation
    _ACADEMIC_TESTS: Dict[str, Tuple[float, float]] = {
        "act":  (1, 36),
        "gmat": (200, 800),
        "sat":  (400, 1600),
        "gre":  (260, 340),
        "cat":  (0, 300),
        "stat": (0, 300),
    }

    # Language tests with their score ranges
    _LANGUAGE_TESTS: Dict[str, Tuple[float, float]] = {
        "ielts":        (0, 9),
        "toefl":        (0, 120),
        "pearson_test": (10, 90),
        "cam_adv_test": (0, 230),
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    major: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    academic_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    graduate_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gmat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gre: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ielts: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    toefl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pearson_test: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cam_adv_test: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inter_bac: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # N StudyBackground  →  1 User  (n-1, FK: user_id)
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="study_bg"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def has_test_scores(self) -> bool:
        """Return True if at least one academic or language test is filled."""
        tests = [
            self.act, self.gmat, self.sat, self.cat, self.gre, self.stat,
            self.ielts, self.toefl, self.pearson_test, self.cam_adv_test,
        ]
        return any(t is not None for t in tests)

    def get_academic_test_summary(self) -> Dict[str, Optional[float]]:
        return {
            k: v for k, v in {
                "act": self.act,
                "gmat": self.gmat,
                "sat": self.sat,
                "cat": self.cat,
                "gre": self.gre,
                "stat": self.stat,
            }.items()
            if v is not None
        }

    def get_language_test_summary(self) -> Dict[str, Optional[float]]:
        return {
            k: v for k, v in {
                "ielts": self.ielts,
                "toefl": self.toefl,
                "pearson_test": self.pearson_test,
                "cam_adv_test": self.cam_adv_test,
                "inter_bac": self.inter_bac,
            }.items()
            if v is not None
        }

    def get_test_summary(self) -> Dict[str, Any]:
        return {
            "academic": self.get_academic_test_summary(),
            "language": self.get_language_test_summary(),
        }

    def get_profile_completeness(self) -> int:
        """Return profile completeness as percentage (0–100)."""
        fields = [
            self.level, self.major, self.academic_rate, self.gpa,
            self.graduate_year,
        ]
        filled = sum(1 for f in fields if f is not None)
        base = int((filled / len(fields)) * 60)
        bonus = 40 if self.has_test_scores() else 0
        return min(base + bonus, 100)

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "StudyBackground":
        obj = cls()
        obj.id = data.get("id")
        obj.user_id = data.get("user_id")
        obj.level = data.get("level")
        obj.major = data.get("major")
        obj.academic_rate = data.get("academic_rate")
        obj.gpa = data.get("gpa")
        obj.graduate_year = data.get("graduate_year")
        obj.act = data.get("act")
        obj.gmat = data.get("gmat")
        obj.sat = data.get("sat")
        obj.cat = data.get("cat")
        obj.gre = data.get("gre")
        obj.stat = data.get("stat")
        obj.ielts = data.get("ielts")
        obj.toefl = data.get("toefl")
        obj.pearson_test = data.get("pearson_test")
        obj.cam_adv_test = data.get("cam_adv_test")
        obj.inter_bac = data.get("inter_bac")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "level": self.level,
            "major": self.major,
            "academic_rate": self.academic_rate,
            "gpa": self.gpa,
            "graduate_year": self.graduate_year,
            "act": self.act,
            "gmat": self.gmat,
            "sat": self.sat,
            "cat": self.cat,
            "gre": self.gre,
            "stat": self.stat,
            "ielts": self.ielts,
            "toefl": self.toefl,
            "pearson_test": self.pearson_test,
            "cam_adv_test": self.cam_adv_test,
            "inter_bac": self.inter_bac,
        }

    def __repr__(self) -> str:
        return (
            f"<StudyBackground id={self.id} user_id={self.user_id} "
            f"level='{self.level}'>"
        )

    # ── Dict-compatible interface (backward compat with router dict access) ───

    def __getitem__(self, key: str):
        return self.to_dict()[key]

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict()

    def items(self):
        return self.to_dict().items()

    def keys(self):
        return self.to_dict().keys()

    def __iter__(self):
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

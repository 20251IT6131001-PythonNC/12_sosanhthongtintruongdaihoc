"""
Entity: University
SQLAlchemy ORM model for the `universities` table.

`scores` and `country_name` are runtime-only aggregated attributes
(populated by the model layer, not stored as DB columns).
"""
from __future__ import annotations
from sqlalchemy import Integer, Float, String, Text, ForeignKey
from app.entities.enums import REGION_LABELS
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .country import Country
    from .detail_infor import DetailInfor
    from .entry_infor import EntryInfor
    from .score import Score
    from .scholarship import Scholarship


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(500), default="")
    country_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("countries.id"), nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank_int: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # N University  →  1 Country       (n-1, FK: country_id)
    country: Mapped[Optional["Country"]] = relationship(
        "Country", back_populates="universities"
    )
    # 1 University  →  1 DetailInfor   (1-1, uselist=False)
    detail_infor: Mapped[Optional["DetailInfor"]] = relationship(
        "DetailInfor", back_populates="university", uselist=False
    )
    # 1 University  →  N EntryInfor    (1-n, mỗi bản ghi là 1 bậc học)
    entry_infors: Mapped[List["EntryInfor"]] = relationship(
        "EntryInfor", back_populates="university"
    )
    # 1 University  →  N Score         (1-n)
    score_list: Mapped[List["Score"]] = relationship(
        "Score", back_populates="university"
    )
    # 1 University  →  N Scholarship   (1-n, cascade delete)
    scholarships: Mapped[List["Scholarship"]] = relationship(
        "Scholarship", back_populates="university", cascade="all, delete-orphan"
    )

    # ── Non-column runtime attributes ─────────────────────────────────────────
    # (aggregated / joined fields populated by the model layer)

    def __init__(self, **kwargs: Any) -> None:
        country_name = kwargs.pop("country_name", None)
        region_id = kwargs.pop("region_id", None)
        scores = kwargs.pop("scores", None)
        super().__init__(**kwargs)
        self._country_name: Optional[str] = country_name
        self._region_id: Optional[int] = region_id
        self._scores: Dict[str, Dict[str, Optional[float]]] = scores or {}

    @property
    def country_name(self) -> Optional[str]:
        if not hasattr(self, "_country_name"):
            self._country_name = None
        return self._country_name

    @country_name.setter
    def country_name(self, value: Optional[str]) -> None:
        self._country_name = value

    @property
    def region_id(self) -> Optional[int]:
        if not hasattr(self, "_region_id"):
            self._region_id = None
        return self._region_id

    @region_id.setter
    def region_id(self, value: Optional[int]) -> None:
        self._region_id = value

    @property
    def scores(self) -> Dict[str, Dict[str, Optional[float]]]:
        if not hasattr(self, "_scores"):
            self._scores = {}
        return self._scores

    @scores.setter
    def scores(self, value: Dict[str, Dict[str, Optional[float]]]) -> None:
        self._scores = value

    # ── Business methods ──────────────────────────────────────────────────────

    def add_score(self, score_type: str, indicator: str, score: float) -> None:
        """Merge one score entry into the aggregated scores dict."""
        if not hasattr(self, "_scores"):
            self._scores = {}
        if score_type not in self._scores:
            self._scores[score_type] = {}
        self._scores[score_type][indicator] = score

    def get_rank_display(self) -> str:
        return f"#{self.rank_int}" if self.rank_int else "Unranked"

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "University":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            region_id=data.get("region_id"),
            country_id=data.get("country_id"),
            city=data.get("city"),
            logo=data.get("logo"),
            overall_score=data.get("overall_score"),
            rank_int=data.get("rank_int") or data.get("rank"),
            path=data.get("path"),
            country_name=data.get("country_name") or data.get("country"),
            scores=data.get("scores"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "region_id": self.region_id,
            "region": REGION_LABELS.get(self.region_id) if self.region_id else None,
            "country_id": self.country_id,
            "city": self.city,
            "logo": self.logo,
            "overall_score": self.overall_score,
            "rank": self.rank_int,
            "rank_int": self.rank_int,
            "path": self.path,
            "country": self.country_name,
            "country_name": self.country_name,
            "scores": self.scores,
        }

    def __repr__(self) -> str:
        return f"<University id={self.id} name='{self.name}' rank={self.rank_int}>"

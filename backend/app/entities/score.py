"""
Entity: Score
SQLAlchemy ORM model for the `scores` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from app.database import Base


if TYPE_CHECKING:
    from .university import University
    from .indicator import Indicator


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("indicators.id"), nullable=True
    )
    rank_int: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id"), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    # N Score  →  1 University   (n-1, FK: university_id)
    university: Mapped[Optional["University"]] = relationship(
        "University", back_populates="score_list"
    )
    # N Score  →  1 Indicator    (n-1, FK: indicator_id)
    indicator: Mapped[Optional["Indicator"]] = relationship(
        "Indicator", back_populates="scores"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_formatted_score(self) -> str:
        """Return score formatted to 2 decimal places or 'N/A'."""
        return f"{self.score:.2f}" if self.score is not None else "N/A"

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Score":
        obj = cls()
        obj.id = data.get("id")
        obj.indicator_id = data.get("indicator_id")
        obj.rank_int = data.get("rank_int")
        obj.score = data.get("score")
        obj.university_id = data.get("university_id")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "indicator_id": self.indicator_id,
            "rank_int": self.rank_int,
            "score": self.score,
            "university_id": self.university_id,
            "indicator_name": self.indicator.name if self.indicator else None,
            "score_type_name": self.indicator.score_type.name if self.indicator and self.indicator.score_type else None,
        }

    def __repr__(self) -> str:
        return f"<Score id={self.id} uni={self.university_id} score={self.score}>"

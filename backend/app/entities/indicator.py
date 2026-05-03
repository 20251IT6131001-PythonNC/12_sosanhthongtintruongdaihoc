"""
Entity: Indicator
SQLAlchemy ORM model for the `indicators` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .score import Score
    from .score_type import ScoreType


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    score_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("score_types.id"), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    # N Indicator  →  1 ScoreType  (n-1, FK: score_type_id)
    score_type: Mapped[Optional["ScoreType"]] = relationship(
        "ScoreType", back_populates="indicators"
    )
    # 1 Indicator  →  N Score  (1-n)
    scores: Mapped[List["Score"]] = relationship(
        "Score", back_populates="indicator"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_display_name(self) -> str:
        return self.name.strip() if self.name else ""

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Indicator":
        obj = cls()
        obj.id = data.get("id")
        obj.name = data.get("name", "")
        obj.score_type_id = data.get("score_type_id")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "score_type_id": self.score_type_id,
        }

    def __repr__(self) -> str:
        return f"<Indicator id={self.id} name='{self.name}'>"

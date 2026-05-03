"""
Entity: ScoreType
SQLAlchemy ORM model for the `score_types` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .score import Score
    from .indicator import Indicator


class ScoreType(Base):
    __tablename__ = "score_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")

    # ── Relationships ──────────────────────────────────────────────────────
    # 1 ScoreType  →  N Indicator  (1-n)
    indicators: Mapped[List["Indicator"]] = relationship(
        "Indicator", back_populates="score_type"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_display_name(self) -> str:
        return self.name.strip() if self.name else ""

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreType":
        obj = cls()
        obj.id = data.get("id")
        obj.name = data.get("name", "")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"<ScoreType id={self.id} name='{self.name}'>"

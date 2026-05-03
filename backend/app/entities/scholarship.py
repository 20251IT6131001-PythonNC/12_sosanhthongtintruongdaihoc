"""
Entity: Scholarship
SQLAlchemy ORM model for the `scholarships` table.
FK: scholarships.university_id → universities.id (ON DELETE CASCADE)
"""
from __future__ import annotations
from sqlalchemy import Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from app.database import Base

if TYPE_CHECKING:
    from .university import University


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, default="")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # N Scholarship  →  1 University  (n-1, FK: university_id, ON DELETE CASCADE)
    university: Mapped[Optional["University"]] = relationship(
        "University", back_populates="scholarships"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_formatted_value(self) -> str:
        """Return scholarship value formatted as currency string."""
        if self.value is None:
            return "N/A"
        return f"${self.value:,.0f}"

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Scholarship":
        obj = cls()
        obj.id = data.get("id")
        obj.university_id = data.get("university_id")
        obj.name = data.get("name", "")
        obj.value = data.get("value")
        obj.duration = data.get("duration")
        obj.criteria = data.get("criteria")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "university_id": self.university_id,
            "name": self.name,
            "value": self.value,
            "duration": self.duration,
            "criteria": self.criteria,
        }

    def __repr__(self) -> str:
        return f"<Scholarship id={self.id} name='{self.name}' uni={self.university_id}>"

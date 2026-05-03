"""
Entity: Country
SQLAlchemy ORM model for the `countries` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.entities.enums import REGION_LABELS
from typing import TYPE_CHECKING, List, Optional
from typing import TYPE_CHECKING, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .university import University
    from .user import User


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    region_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    # 1 Country  →  N University  (1-n)
    universities: Mapped[List["University"]] = relationship(
        "University", back_populates="country"
    )
    # 1 Country  →  N User        (1-n)
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="country"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_display_name(self) -> str:
        """Return country name with title-case."""
        return self.name.title() if self.name else ""

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Country":
        obj = cls()
        obj.id = data.get("id")
        obj.name = data.get("name", "")
        obj.region_id = data.get("region_id")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "region_id": self.region_id,
            "region": REGION_LABELS.get(self.region_id) if self.region_id else None,
        }

    def __repr__(self) -> str:
        return f"<Country id={self.id} name='{self.name}'>"

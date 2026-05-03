"""
Entity: User
SQLAlchemy ORM model for the `users` table.

DB column name mapping for email verification fields:
  email_verification_code  →  email_verification_token (DB column)
  email_verification_expiry → verification_token_expiry (DB column)
"""
from __future__ import annotations
from sqlalchemy import Integer, Boolean, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional
from app.database import Base

if TYPE_CHECKING:
    from .country import Country
    from .study_bg import StudyBackground


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255), default="")
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gender: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("countries.id"), nullable=True
    )
    main_lang: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    add_lang: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ethnic_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    special: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_type: Mapped[int] = mapped_column(Integer, default=1)
    insert_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    # Python attr name differs from DB column name
    email_verification_code: Mapped[Optional[str]] = mapped_column(
        "email_verification_token", String(255), nullable=True
    )
    email_verification_expiry: Mapped[Optional[datetime]] = mapped_column(
        "verification_token_expiry", DateTime, nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    # N User  →  1 Country         (n-1, FK: country_id)
    country: Mapped[Optional["Country"]] = relationship(
        "Country", back_populates="users"
    )
    # 1 User  →  1 StudyBackground  (1-1, uselist=False)
    study_bg: Mapped[Optional["StudyBackground"]] = relationship(
        "StudyBackground", back_populates="user", uselist=False
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @validates("email")
    def _normalize_email(self, key: str, value: str) -> str:
        return value.lower().strip() if value else value

    # ── Business methods ──────────────────────────────────────────────────────

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_personal_info(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.get_full_name(),
            "email": self.email,
            "phone_number": self.phone_number,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "country_id": self.country_id,
            "main_lang": self.main_lang,
            "add_lang": self.add_lang,
            "ethnic_group": self.ethnic_group,
            "special": self.special,
            "image": self.image,
        }

    def is_admin(self) -> bool:
        return self.role_type == 2

    def is_email_verified(self) -> bool:
        return bool(self.email_verified)

    def verify_login(self, plain_password: str) -> bool:
        from app.utils.security import verify_password
        return verify_password(plain_password, self.password)

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        obj = cls()
        obj.id = data.get("id")
        obj.first_name = data.get("first_name", "")
        obj.last_name = data.get("last_name", "")
        obj.email = data.get("email", "")
        obj.password = data.get("password", "")
        obj.image = data.get("image")
        obj.phone_number = data.get("phone_number")
        obj.gender = data.get("gender")
        obj.dob = data.get("dob")
        obj.country_id = data.get("country_id")
        obj.main_lang = data.get("main_lang")
        obj.add_lang = data.get("add_lang")
        obj.ethnic_group = data.get("ethnic_group")
        obj.special = data.get("special")
        obj.role_type = data.get("role_type", 1)
        obj.insert_date = data.get("insert_date")
        obj.update_date = data.get("update_date")
        obj.postal_code = data.get("postal_code")
        obj.email_verified = bool(data.get("email_verified", False))
        obj.email_verification_code = (
            data.get("email_verification_code")
            or data.get("email_verification_token")
        )
        obj.email_verification_expiry = (
            data.get("email_verification_expiry")
            or data.get("verification_token_expiry")
        )
        return obj

    def to_dict(self) -> dict:
        """Serialize entity to plain dict (excludes password)."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "image": self.image,
            "phone_number": self.phone_number,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "country_id": self.country_id,
            "main_lang": self.main_lang,
            "add_lang": self.add_lang,
            "ethnic_group": self.ethnic_group,
            "special": self.special,
            "role_type": self.role_type,
            "insert_date": self.insert_date.isoformat() if self.insert_date else None,
            "update_date": self.update_date.isoformat() if self.update_date else None,
            "postal_code": self.postal_code,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "reason": self.reason,
        }

    def to_dict_with_password(self) -> dict:
        """Full dict including password (for internal auth use)."""
        d = self.to_dict()
        d["password"] = self.password
        return d

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role={self.role_type}>"

    # ── Dict-compatible interface (backward compat with router dict access) ───

    def __getitem__(self, key: str) -> Any:
        return self.to_dict_with_password()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict_with_password().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict_with_password()

    def items(self):
        return self.to_dict_with_password().items()

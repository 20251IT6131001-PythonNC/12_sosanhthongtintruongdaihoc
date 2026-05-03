"""
One-shot script: writes all 10 SQLAlchemy ORM entity files.
Run from repo root:  python backend/write_orm_entities.py
"""
import pathlib

BASE = pathlib.Path(__file__).parent / "app" / "entities"

FILES = {}

# ─────────────────────────────── country.py ──────────────────────────────────
FILES["country.py"] = '''\
"""
Entity: Country
SQLAlchemy ORM model for the `countries` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .university import University
    from .user import User


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), default="")

    # Relationships
    universities: Mapped[List["University"]] = relationship(
        "University", back_populates="country"
    )
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
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"<Country id={self.id} name=\'{self.name}\'>"
'''

# ─────────────────────────────── indicator.py ────────────────────────────────
FILES["indicator.py"] = '''\
"""
Entity: Indicator
SQLAlchemy ORM model for the `indicators` table.
"""
from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional
from app.database import Base

if TYPE_CHECKING:
    from .score import Score


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")

    # Relationships
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
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"<Indicator id={self.id} name=\'{self.name}\'>"
'''

# ─────────────────────────────── score_type.py ───────────────────────────────
FILES["score_type.py"] = '''\
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


class ScoreType(Base):
    __tablename__ = "score_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="")

    # Relationships
    scores: Mapped[List["Score"]] = relationship(
        "Score", back_populates="score_type"
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
        return f"<ScoreType id={self.id} name=\'{self.name}\'>"
'''

# ─────────────────────────────── score.py ────────────────────────────────────
FILES["score.py"] = '''\
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
    from .score_type import ScoreType


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("indicators.id"), nullable=True
    )
    score_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("score_types.id"), nullable=True
    )
    rank_int: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    university_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universities.id"), nullable=True
    )

    # Relationships
    university: Mapped[Optional["University"]] = relationship(
        "University", back_populates="score_list"
    )
    indicator: Mapped[Optional["Indicator"]] = relationship(
        "Indicator", back_populates="scores"
    )
    score_type: Mapped[Optional["ScoreType"]] = relationship(
        "ScoreType", back_populates="scores"
    )

    # ── Business methods ──────────────────────────────────────────────────────

    def get_formatted_score(self) -> str:
        """Return score formatted to 2 decimal places or \'N/A\'."""
        return f"{self.score:.2f}" if self.score is not None else "N/A"

    # ── Factory / serialization ───────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Score":
        obj = cls()
        obj.id = data.get("id")
        obj.indicator_id = data.get("indicator_id")
        obj.score_type_id = data.get("score_type_id")
        obj.rank_int = data.get("rank_int")
        obj.score = data.get("score")
        obj.university_id = data.get("university_id")
        return obj

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "indicator_id": self.indicator_id,
            "score_type_id": self.score_type_id,
            "rank_int": self.rank_int,
            "score": self.score,
            "university_id": self.university_id,
            "indicator_name": self.indicator.name if self.indicator else None,
            "score_type_name": self.score_type.name if self.score_type else None,
        }

    def __repr__(self) -> str:
        return f"<Score id={self.id} uni={self.university_id} score={self.score}>"
'''

# ─────────────────────────────── scholarship.py ──────────────────────────────
FILES["scholarship.py"] = '''\
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

    # Relationships
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
        return f"<Scholarship id={self.id} name=\'{self.name}\' uni={self.university_id}>"
'''

# ─────────────────────────────── detail_infor.py ─────────────────────────────
FILES["detail_infor.py"] = '''\
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

    # Relationships
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
'''

# ─────────────────────────────── entry_infor.py ──────────────────────────────
FILES["entry_infor.py"] = '''\
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
        1: "Bachelor\'s Degree",
        2: "Master\'s Degree",
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

    # Relationships
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
'''

# ─────────────────────────────── university.py ───────────────────────────────
FILES["university.py"] = '''\
"""
Entity: University
SQLAlchemy ORM model for the `universities` table.

`scores` and `country_name` are runtime-only aggregated attributes
(populated by the model layer, not stored as DB columns).
"""
from __future__ import annotations
from sqlalchemy import Integer, Float, String, Text, ForeignKey
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
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("countries.id"), nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank_int: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    country: Mapped[Optional["Country"]] = relationship(
        "Country", back_populates="universities"
    )
    detail_infor: Mapped[Optional["DetailInfor"]] = relationship(
        "DetailInfor", back_populates="university", uselist=False
    )
    entry_infors: Mapped[List["EntryInfor"]] = relationship(
        "EntryInfor", back_populates="university"
    )
    score_list: Mapped[List["Score"]] = relationship(
        "Score", back_populates="university"
    )
    scholarships: Mapped[List["Scholarship"]] = relationship(
        "Scholarship", back_populates="university", cascade="all, delete-orphan"
    )

    # ── Non-column runtime attributes ─────────────────────────────────────────
    # (aggregated / joined fields populated by the model layer)

    def __init__(self, **kwargs: Any) -> None:
        country_name = kwargs.pop("country_name", None)
        scores = kwargs.pop("scores", None)
        super().__init__(**kwargs)
        self._country_name: Optional[str] = country_name
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
            region=data.get("region"),
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
            "region": self.region,
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
        return f"<University id={self.id} name=\'{self.name}\' rank={self.rank_int}>"
'''

# ─────────────────────────────── study_bg.py ─────────────────────────────────
FILES["study_bg.py"] = '''\
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
    inter_bac: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
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
            f"level=\'{self.level}\'>"
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
'''

# ─────────────────────────────── user.py ─────────────────────────────────────
FILES["user.py"] = '''\
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
    # Python attr name differs from DB column name
    email_verification_code: Mapped[Optional[str]] = mapped_column(
        "email_verification_token", String(255), nullable=True
    )
    email_verification_expiry: Mapped[Optional[datetime]] = mapped_column(
        "verification_token_expiry", DateTime, nullable=True
    )

    # Relationships
    country: Mapped[Optional["Country"]] = relationship(
        "Country", back_populates="users"
    )
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
        }

    def to_dict_with_password(self) -> dict:
        """Full dict including password (for internal auth use)."""
        d = self.to_dict()
        d["password"] = self.password
        return d

    def __repr__(self) -> str:
        return f"<User id={self.id} email=\'{self.email}\' role={self.role_type}>"

    # ── Dict-compatible interface (backward compat with router dict access) ───

    def __getitem__(self, key: str) -> Any:
        return self.to_dict_with_password()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict_with_password().get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.to_dict_with_password()

    def items(self):
        return self.to_dict_with_password().items()
'''

# ─────────────────────────────── write files ─────────────────────────────────
for filename, content in FILES.items():
    path = BASE / filename
    path.write_text(content, encoding="utf-8")
    print(f"  Written: {path}")

print("\nAll entity files written successfully.")

"""
Country Model - Data access layer for countries table (SQLAlchemy ORM).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.entities.country import Country
from app.entities.enums import REGION_LABELS
from typing import Optional, List


class CountryModel:
    """Country data access layer"""

    @staticmethod
    def get_by_id(db: Session, country_id: int) -> Optional[Country]:
        return db.query(Country).filter(Country.id == country_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Country]:
        return (
            db.query(Country)
            .filter(func.lower(Country.name) == name.lower())
            .first()
        )

    @staticmethod
    def search_by_name(db: Session, name: str) -> List[dict]:
        results = (
            db.query(Country)
            .filter(Country.name.ilike(f"%{name}%"))
            .order_by(Country.name)
            .limit(50)
            .all()
        )
        return [r.to_dict() for r in results]

    @staticmethod
    def get_all(db: Session) -> List[dict]:
        results = db.query(Country).order_by(Country.name).all()
        return [r.to_dict() for r in results]

    @staticmethod
    def get_id_by_name(db: Session, name: str) -> Optional[int]:
        country = CountryModel.get_by_name(db, name)
        return country.id if country else None

    @staticmethod
    def get_by_region_id(db: Session, region_id: int) -> List[dict]:
        results = (
            db.query(Country)
            .filter(Country.region_id == region_id)
            .order_by(Country.name)
            .all()
        )
        return [r.to_dict() for r in results]

    @staticmethod
    def get_all_regions(db: Session) -> List[dict]:
        """Return list of {id, name} for all regions that have at least one country."""
        used_ids = (
            db.query(Country.region_id)
            .filter(Country.region_id.isnot(None))
            .distinct()
            .all()
        )
        ids = sorted({row[0] for row in used_ids})
        return [{"id": rid, "name": REGION_LABELS[rid]} for rid in ids if rid in REGION_LABELS]

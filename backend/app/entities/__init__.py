"""
Entity layer — OOP representations of database tables.

Each entity class mirrors a DB table row and exposes:
  - Typed fields with defaults
  - from_dict() classmethod: construct from a raw DB row / dict
  - to_dict()             : serialize back to plain dict
  - Business methods / computed properties

Import everything via:
    from app.entities import User, University, Country, StudyBackground, ...
"""

from app.entities.user import User
from app.entities.university import University
from app.entities.country import Country
from app.entities.study_bg import StudyBackground
from app.entities.detail_infor import DetailInfor
from app.entities.entry_infor import EntryInfor
from app.entities.indicator import Indicator
from app.entities.score import Score
from app.entities.score_type import ScoreType
from app.entities.scholarship import Scholarship

__all__ = [
    "User",
    "University",
    "Country",
    "StudyBackground",
    "DetailInfor",
    "EntryInfor",
    "Indicator",
    "Score",
    "ScoreType",
    "Scholarship",
]

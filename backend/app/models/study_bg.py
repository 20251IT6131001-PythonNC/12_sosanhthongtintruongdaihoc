"""
Study Background Model - Data access layer for study_bg table (SQLAlchemy ORM).
"""
from sqlalchemy.orm import Session
from app.entities.study_bg import StudyBackground
from typing import Optional, Tuple, Dict, Any


class StudyBGModel:
    """Study Background data access layer"""

    @staticmethod
    def create_default(db: Session, user_id: int) -> bool:
        """Create an empty study background row for a new user."""
        try:
            bg = StudyBackground(user_id=user_id)
            db.add(bg)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error creating study background: {e}")
            return False

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[StudyBackground]:
        try:
            return (
                db.query(StudyBackground)
                .filter(StudyBackground.user_id == user_id)
                .first()
            )
        except Exception as e:
            print(f"Error getting study background: {e}")
            return None

    @staticmethod
    def update(db: Session, user_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            db.query(StudyBackground).filter(
                StudyBackground.user_id == user_id
            ).update(
                {
                    StudyBackground.level:         data.get("level"),
                    StudyBackground.major:         data.get("major"),
                    StudyBackground.academic_rate: data.get("academic_rate"),
                    StudyBackground.gpa:           data.get("gpa"),
                    StudyBackground.graduate_year: data.get("graduate_year"),
                    StudyBackground.act:           data.get("act"),
                    StudyBackground.gmat:          data.get("gmat"),
                    StudyBackground.sat:           data.get("sat"),
                    StudyBackground.cat:           data.get("cat"),
                    StudyBackground.gre:           data.get("gre"),
                    StudyBackground.stat:          data.get("stat"),
                    StudyBackground.ielts:         data.get("ielts"),
                    StudyBackground.toefl:         data.get("toefl"),
                    StudyBackground.pearson_test:  data.get("pearson_test"),
                    StudyBackground.cam_adv_test:  data.get("cam_adv_test"),
                    StudyBackground.inter_bac:     data.get("inter_bac"),
                },
                synchronize_session=False,
            )
            db.commit()
            return True, "Cập nhật thông tin học tập thành công"
        except Exception as e:
            db.rollback()
            print(f"Error updating study background: {e}")
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        try:
            db.query(StudyBackground).filter(
                StudyBackground.user_id == user_id
            ).delete(synchronize_session=False)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting study background: {e}")
            return False

    @staticmethod
    def count_completed_fields(db: Session, user_id: int) -> int:
        try:
            bg = StudyBGModel.get_by_user_id(db, user_id)
            if not bg:
                return 0
            return sum(
                1
                for k, v in bg.items()
                if k not in ("id", "user_id") and v is not None
            )
        except Exception as e:
            print(f"Error counting fields: {e}")
            return 0

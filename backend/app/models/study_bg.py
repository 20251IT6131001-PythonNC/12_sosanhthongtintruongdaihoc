"""
Study Background Model - Data access layer for study_bg table.
Adapted from existing models/StudyBGModel.py
"""
from app.database import execute_query
from typing import Optional, Dict, Any, Tuple


class StudyBGModel:
    """Study Background data access layer"""

    @staticmethod
    def create_default(user_id: int) -> bool:
        """
        Create default study background for new user.

        Args:
            user_id: User's ID

        Returns:
            True if successful, False otherwise
        """
        try:
            sql = """
                INSERT INTO study_bg (
                    user_id, level, major, academic_rate, gpa,
                    graduate_year, act, gmat, sat,
                    cat, gre, stat, ielts, toefl,
                    pearson_test, cam_adv_test, inter_bac
                )
                VALUES (
                    %s, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL
                )
            """
            execute_query(sql, (user_id,))
            return True
        except Exception as e:
            print(f"Error creating study background: {e}")
            return False

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get study background by user ID.

        Args:
            user_id: User's ID

        Returns:
            Study background dict if found, None otherwise
        """
        try:
            sql = "SELECT * FROM study_bg WHERE user_id = %s"
            result = execute_query(sql, (user_id,), fetch=True, fetch_one=True)
            return result
        except Exception as e:
            print(f"Error getting study background: {e}")
            return None

    @staticmethod
    def update(user_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update study background.

        Args:
            user_id: User's ID
            data: Dictionary with fields to update

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            sql = """
                UPDATE study_bg
                SET 
                    level = %s,
                    major = %s,
                    academic_rate = %s,
                    gpa = %s,
                    graduate_year = %s,
                    act = %s,
                    gmat = %s,
                    sat = %s,
                    cat = %s,
                    gre = %s,
                    stat = %s,
                    ielts = %s,
                    toefl = %s,
                    pearson_test = %s,
                    cam_adv_test = %s,
                    inter_bac = %s
                WHERE user_id = %s
            """

            execute_query(sql, (
                data.get('level'),
                data.get('major'),
                data.get('academic_rate'),
                data.get('gpa'),
                data.get('graduate_year'),
                data.get('act'),
                data.get('gmat'),
                data.get('sat'),
                data.get('cat'),
                data.get('gre'),
                data.get('stat'),
                data.get('ielts'),
                data.get('toefl'),
                data.get('pearson_test'),
                data.get('cam_adv_test'),
                data.get('inter_bac'),
                user_id
            ))

            return True, "Cập nhật thông tin học tập thành công"
        except Exception as e:
            print(f"Error updating study background: {e}")
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def delete(user_id: int) -> bool:
        """
        Delete study background (when user account is deleted).

        Args:
            user_id: User's ID

        Returns:
            True if successful, False otherwise
        """
        try:
            sql = "DELETE FROM study_bg WHERE user_id = %s"
            execute_query(sql, (user_id,))
            return True
        except Exception as e:
            print(f"Error deleting study background: {e}")
            return False

    @staticmethod
    def count_completed_fields(user_id: int) -> int:
        """
        Count how many fields are filled in study background (for profile completion).

        Args:
            user_id: User's ID

        Returns:
            Number of non-null fields
        """
        try:
            bg = StudyBGModel.get_by_user_id(user_id)
            if not bg:
                return 0

            # Count non-null fields (excluding user_id and id)
            count = sum(1 for k, v in bg.items() if k not in ['id', 'user_id'] and v is not None)
            return count
        except Exception as e:
            print(f"Error counting fields: {e}")
            return 0

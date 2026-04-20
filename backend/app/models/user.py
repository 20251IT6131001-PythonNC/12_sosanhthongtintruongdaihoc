"""
User Model - Data access layer for users table.
Adapted from existing models/UserModel.py
"""
from app.database import execute_query, get_db_connection
from app.utils.security import hash_password, verify_password
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


class UserModel:
    """User data access layer"""

    @staticmethod
    def create_user(first_name: str, last_name: str, email: str, password: str, role_type: int = 1) -> Tuple[bool, int]:
        """
        Create a new user.

        Args:
            first_name: User's first name
            last_name: User's last name
            email: User's email
            password: Plain-text password (will be hashed)
            role_type: 1 for user, 2 for admin (default: 1)

        Returns:
            Tuple of (success: bool, user_id: int)
        """
        sql = """
            INSERT INTO users (
                first_name, last_name, email, password, insert_date, update_date, role_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        now = datetime.now()
        hashed_password = hash_password(password)

        try:
            user_id = execute_query(sql, (first_name, last_name, email, hashed_password, now, now, role_type))
            return True, user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return False, 0

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.

        Args:
            email: User's email

        Returns:
            User dict if found, None otherwise
        """
        sql = "SELECT * FROM users WHERE email = %s"
        try:
            user = execute_query(sql, (email,), fetch=True, fetch_one=True)
            return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: User's ID

        Returns:
            User dict if found, None otherwise
        """
        sql = "SELECT * FROM users WHERE id = %s"
        try:
            user = execute_query(sql, (user_id,), fetch=True, fetch_one=True)
            return user
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    @staticmethod
    def update_user(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update user profile.

        Args:
            data: Dict containing user fields to update (must include "id")

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not data.get("id"):
            return False, "Không tìm thấy ID người dùng"

        try:
            sql = """
                UPDATE users SET
                    first_name=%s,
                    last_name=%s,
                    email=%s,
                    phone_number=%s,
                    country_id=%s,
                    gender=%s,
                    dob=%s,
                    postal_code=%s,
                    ethnic_group=%s,
                    main_lang=%s,
                    add_lang=%s,
                    special=%s,
                    update_date=NOW()
                WHERE id=%s
            """

            execute_query(sql, (
                data["first_name"],
                data["last_name"],
                data["email"],
                data.get("phone_number"),
                data.get("country_id"),
                data.get("gender"),
                data.get("dob"),
                data.get("postal_code"),
                data.get("ethnic_group"),
                data.get("main_lang"),
                data.get("add_lang"),
                data.get("special"),
                data["id"]
            ))

            return True, "Cập nhật thông tin thành công!"

        except Exception as e:
            return False, f"Lỗi DB: {str(e)}"

    @staticmethod
    def update_password(user_id: int, new_password: str) -> Tuple[bool, str]:
        """
        Update user password.

        Args:
            user_id: User's ID
            new_password: New plain-text password (will be hashed)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            new_hash = hash_password(new_password)
            sql = "UPDATE users SET password = %s, update_date=NOW() WHERE id = %s"
            execute_query(sql, (new_hash, user_id))
            return True, "Cập nhật mật khẩu thành công"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def get_all_users(page: int = 1, limit: int = 20) -> Tuple[list, int]:
        """
        Get all users with pagination.

        Args:
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            Tuple of (users: list, total: int)
        """
        try:
            offset = (page - 1) * limit

            # Get total count
            count_sql = "SELECT COUNT(*) as total FROM users"
            count_result = execute_query(count_sql, fetch=True, fetch_one=True)
            total = count_result['total'] if count_result else 0

            # Get paginated users
            users_sql = "SELECT * FROM users ORDER BY id DESC LIMIT %s OFFSET %s"
            users = execute_query(users_sql, (limit, offset), fetch=True)

            return users or [], total

        except Exception as e:
            print(f"Error getting all users: {e}")
            return [], 0

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """
        Delete a user.

        Args:
            user_id: User's ID

        Returns:
            True if successful, False otherwise
        """
        try:
            sql = "DELETE FROM users WHERE id = %s"
            execute_query(sql, (user_id,))
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    @staticmethod
    def is_admin(role_type: int) -> bool:
        """Check if user is admin"""
        return role_type == 2

    @staticmethod
    def verify_email(user_id: int) -> Tuple[bool, str]:
        """
        Mark email as verified for a user.

        Args:
            user_id: User's ID

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            sql = """
                UPDATE users
                SET email_verified = TRUE, email_verification_token = NULL, verification_token_expiry = NULL
                WHERE id = %s
            """
            execute_query(sql, (user_id,))
            return True, "Email verified successfully"
        except Exception as e:
            print(f"Error verifying email: {e}")
            return False, f"Error: {str(e)}"

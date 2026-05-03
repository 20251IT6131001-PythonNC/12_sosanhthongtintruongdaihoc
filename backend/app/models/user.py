"""
User Model - Data access layer for users table (SQLAlchemy ORM).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.entities.user import User
from app.utils.security import hash_password
from datetime import datetime
from typing import Optional, Tuple, List


class UserModel:
    """User data access layer"""

    @staticmethod
    def create_user(
        db: Session,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_type: int = 1,
        email_verified: bool = False,
    ) -> Tuple[bool, int]:
        """Create a new user. Returns (success, user_id)."""
        try:
            now = datetime.now()
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hash_password(password),
                role_type=role_type,
                email_verified=email_verified,
                insert_date=now,
                update_date=now,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return True, user.id
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {e}")
            return False, 0

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        try:
            return db.query(User).filter(User.email == email.lower().strip()).first()
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    @staticmethod
    def update_user(db: Session, data: dict) -> Tuple[bool, str]:
        if not data.get("id"):
            return False, "Không tìm thấy ID người dùng"
        try:
            db.query(User).filter(User.id == data["id"]).update(
                {
                    User.first_name:   data["first_name"],
                    User.last_name:    data["last_name"],
                    User.email:        data["email"],
                    User.phone_number: data.get("phone_number"),
                    User.country_id:   data.get("country_id"),
                    User.gender:       data.get("gender"),
                    User.dob:          data.get("dob"),
                    User.postal_code:  data.get("postal_code"),
                    User.ethnic_group: data.get("ethnic_group"),
                    User.main_lang:    data.get("main_lang"),
                    User.add_lang:     data.get("add_lang"),
                    User.special:      data.get("special"),
                    User.update_date:  datetime.now(),
                },
                synchronize_session=False,
            )
            db.commit()
            return True, "Cập nhật thông tin thành công!"
        except Exception as e:
            db.rollback()
            return False, f"Lỗi DB: {str(e)}"

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> Tuple[bool, str]:
        try:
            db.query(User).filter(User.id == user_id).update(
                {User.password: hash_password(new_password), User.update_date: datetime.now()},
                synchronize_session=False,
            )
            db.commit()
            return True, "Cập nhật mật khẩu thành công"
        except Exception as e:
            db.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def close_account(db: Session, user_id: int, reason: str) -> Tuple[bool, str]:
        """Deactivate user account and store closure reason."""
        try:
            db.query(User).filter(User.id == user_id).update(
                {User.is_active: False, User.reason: reason, User.update_date: datetime.now()},
                synchronize_session=False,
            )
            db.commit()
            return True, "Tài khoản đã được đóng"
        except Exception as e:
            db.rollback()
            return False, f"Lỗi: {str(e)}"

    @staticmethod
    def get_all_users(db: Session, page: int = 1, limit: int = 20) -> Tuple[List[dict], int]:
        try:
            offset = (page - 1) * limit
            total = db.query(User).count()
            users = (
                db.query(User)
                .order_by(User.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [u.to_dict() for u in users], total
        except Exception as e:
            print(f"Error getting all users: {e}")
            return [], 0

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        try:
            db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting user: {e}")
            return False

    @staticmethod
    def is_admin(role_type: int) -> bool:
        return role_type == 2

    @staticmethod
    def verify_email(db: Session, user_id: int) -> Tuple[bool, str]:
        try:
            db.query(User).filter(User.id == user_id).update(
                {
                    User.email_verified:         True,
                    User.email_verification_code: None,
                    User.email_verification_expiry: None,
                },
                synchronize_session=False,
            )
            db.commit()
            return True, "Email verified successfully"
        except Exception as e:
            db.rollback()
            print(f"Error verifying email: {e}")
            return False, f"Error: {str(e)}"

    # ── Verification-code helpers (DB-backed, safe across restarts) ───────────

    @staticmethod
    def create_pending_user(
        db: Session,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        code: str,
        expiry: datetime,
    ) -> Tuple[bool, str]:
        """
        Create a user with email_verified=False and store OTP in DB.
        If the email already exists but is unverified, update the code (resend case).
        Returns (True, "") on success or (False, error_message).
        """
        try:
            existing = db.query(User).filter(User.email == email.lower().strip()).first()
            if existing:
                if existing.email_verified and existing.is_active:
                    return False, "Email already registered"
                # Allow resend (unverified) OR re-register (closed account):
                # reset all fields including is_active and reason
                existing.first_name = first_name
                existing.last_name = last_name
                existing.password = hash_password(password)
                existing.email_verification_code = code
                existing.email_verification_expiry = expiry
                existing.email_verified = False
                existing.is_active = True
                existing.reason = None
                existing.update_date = datetime.now()
                db.commit()
                return True, ""
            now = datetime.now()
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=hash_password(password),
                role_type=1,
                email_verified=False,
                email_verification_code=code,
                email_verification_expiry=expiry,
                insert_date=now,
                update_date=now,
            )
            db.add(user)
            db.commit()
            return True, ""
        except Exception as e:
            db.rollback()
            print(f"Error creating pending user: {e}")
            return False, str(e)

    @staticmethod
    def verify_and_activate(db: Session, email: str, code: str) -> Tuple[bool, any]:
        """
        Verify signup OTP from DB and activate the account.
        Returns (True, user_id) on success or (False, error_message).
        """
        try:
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if not user or not user.email_verification_code or not user.email_verification_expiry:
                return False, "Verification code not found or expired"
            if user.email_verified:
                return False, "Account already verified"
            if datetime.now() > user.email_verification_expiry:
                return False, "Verification code has expired"
            if user.email_verification_code != code:
                return False, "Invalid verification code"
            # Activate
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_expiry = None
            user.update_date = datetime.now()
            db.commit()
            return True, user.id
        except Exception as e:
            db.rollback()
            print(f"Error activating user: {e}")
            return False, str(e)

    @staticmethod
    def store_reset_code(db: Session, user_id: int, code: str, expiry: datetime) -> bool:
        """Store a forgot-password OTP in the DB (reuses email_verification columns)."""
        try:
            db.query(User).filter(User.id == user_id).update(
                {
                    User.email_verification_code: code,
                    User.email_verification_expiry: expiry,
                },
                synchronize_session=False,
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error storing reset code: {e}")
            return False

    @staticmethod
    def verify_reset_code(db: Session, email: str, code: str) -> Tuple[bool, any]:
        """
        Verify forgot-password OTP from DB.
        Clears the code on success.
        Returns (True, user_id) on success or (False, error_message).
        """
        try:
            user = db.query(User).filter(User.email == email.lower().strip()).first()
            if not user or not user.email_verification_code or not user.email_verification_expiry:
                return False, "Verification code not found or expired. Please request a new code."
            if datetime.now() > user.email_verification_expiry:
                user.email_verification_code = None
                user.email_verification_expiry = None
                db.commit()
                return False, "Verification code has expired. Please request a new code."
            if user.email_verification_code != code:
                return False, "Verification code is incorrect"
            # Clear code after use
            user.email_verification_code = None
            user.email_verification_expiry = None
            db.commit()
            return True, user.id
        except Exception as e:
            db.rollback()
            print(f"Error verifying reset code: {e}")
            return False, str(e)

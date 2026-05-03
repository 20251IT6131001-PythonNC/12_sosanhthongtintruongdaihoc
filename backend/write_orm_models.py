"""
One-shot script: writes new SQLAlchemy ORM-based model files.
Run from repo root:  python backend/write_orm_models.py
"""
import pathlib

BASE = pathlib.Path(__file__).parent / "app" / "models"

FILES = {}

# ─────────────────────────────── country.py ──────────────────────────────────
FILES["country.py"] = '''\
"""
Country Model - Data access layer for countries table (SQLAlchemy ORM).
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.entities.country import Country
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
'''

# ─────────────────────────────── user.py ─────────────────────────────────────
FILES["user.py"] = '''\
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
'''

# ─────────────────────────────── study_bg.py ─────────────────────────────────
FILES["study_bg.py"] = '''\
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
'''

# ─────────────────────────────── university.py ───────────────────────────────
FILES["university.py"] = '''\
"""
University Model - Data access layer for universities (SQLAlchemy ORM session).

Complex multi-JOIN queries use db.execute(text(...)) with named bind params.
Simple lookups use db.query(University) ORM syntax.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.entities.university import University
from app.entities.detail_infor import DetailInfor
from app.entities.entry_infor import EntryInfor
from typing import Optional, Dict, Any, List


_SCORE_JOIN_SELECT = """
    u.id,
    u.rank_int,
    u.overall_score,
    u.name        AS university_name,
    u.city,
    c.name        AS country_name,
    u.logo,
    st.name       AS score_type,
    i.name        AS indicator_name,
    s.score
"""

_SCORE_JOINS = """
    LEFT JOIN countries   c  ON u.country_id  = c.id
    LEFT JOIN scores      s  ON u.id          = s.university_id
    LEFT JOIN score_types st ON s.score_type_id = st.id
    LEFT JOIN indicators  i  ON i.id          = s.indicator_id
"""


def _build_uni_map(rows) -> Dict[int, University]:
    """Group flat JOIN rows into a dict of University entities keyed by id."""
    uni_map: Dict[int, University] = {}
    for row in rows:
        row = dict(row)
        uid = row["id"]
        if uid not in uni_map:
            uni_map[uid] = University(
                id=row["id"],
                rank_int=row["rank_int"],
                overall_score=row["overall_score"] or 0.0,
                name=row["university_name"],
                city=row["city"],
                country_name=row["country_name"],
                logo=row["logo"],
            )
        if row["score_type"] and row["indicator_name"]:
            uni_map[uid].add_score(row["score_type"], row["indicator_name"], row["score"])
    return uni_map


class UniversityModel:

    @staticmethod
    def get_all_universities(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        sql = text(f"""
            SELECT {_SCORE_JOIN_SELECT}
            FROM (
                SELECT id, rank_int, overall_score, name, city, country_id, logo
                FROM universities
                ORDER BY rank_int ASC, id ASC
                LIMIT :limit
            ) u
            {_SCORE_JOINS}
            ORDER BY u.rank_int ASC, u.id ASC
        """)
        rows = db.execute(sql, {"limit": limit}).mappings().all()
        return [u.to_dict() for u in _build_uni_map(rows).values()]

    @staticmethod
    def search_universities_by_name(db: Session, name: str) -> List[Dict[str, Any]]:
        sql = text(f"""
            SELECT {_SCORE_JOIN_SELECT}
            FROM universities u
            {_SCORE_JOINS}
            WHERE u.name LIKE :pattern
            ORDER BY u.rank_int ASC
            LIMIT 50
        """)
        rows = db.execute(sql, {"pattern": f"%{name}%"}).mappings().all()
        return [u.to_dict() for u in _build_uni_map(rows).values()]

    @staticmethod
    def get_regions(db: Session) -> List[str]:
        sql = text(
            "SELECT DISTINCT region FROM universities "
            "WHERE region IS NOT NULL AND region != \\'\\' ORDER BY region ASC"
        )
        rows = db.execute(sql).mappings().all()
        return [r["region"] for r in rows]

    @staticmethod
    def get_countries_by_region(db: Session, region: Optional[str] = None) -> List[Dict[str, Any]]:
        if region:
            sql = text("""
                SELECT DISTINCT c.id, c.name
                FROM universities u
                JOIN countries c ON u.country_id = c.id
                WHERE u.region = :region
                ORDER BY c.name ASC
            """)
            rows = db.execute(sql, {"region": region}).mappings().all()
        else:
            sql = text("""
                SELECT DISTINCT c.id, c.name
                FROM universities u
                JOIN countries c ON u.country_id = c.id
                ORDER BY c.name ASC
            """)
            rows = db.execute(sql).mappings().all()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    TEST_COLUMN_MAP = {
        "IELTS": "IELTS",
        "TOEFL": "TOEFL",
        "SAT":   "SAT",
        "GRE":   "GRE",
        "GMAT":  "GMAT",
        "ACT":   "ACT",
        "ATAR":  "ATAR",
        "GPA":   "GPA",
    }

    @staticmethod
    def filter_universities(
        db: Session,
        region: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        min_rank: Optional[int] = None,
        max_rank: Optional[int] = None,
        english_tests: Optional[List[str]] = None,
        academic_tests: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        where_clauses = ["1=1"]
        params: Dict[str, Any] = {}

        if region:
            where_clauses.append("u.region = :region")
            params["region"] = region
        if country:
            where_clauses.append("c.name = :country_name")
            params["country_name"] = country
        if city:
            where_clauses.append("u.city LIKE :city")
            params["city"] = f"%{city}%"
        if min_rank is not None:
            where_clauses.append("u.rank_int >= :min_rank")
            params["min_rank"] = min_rank
        if max_rank is not None:
            where_clauses.append("u.rank_int <= :max_rank")
            params["max_rank"] = max_rank

        all_tests = list(english_tests or []) + list(academic_tests or [])
        for test_name in all_tests:
            col = UniversityModel.TEST_COLUMN_MAP.get(test_name)
            if col:
                where_clauses.append(
                    f"EXISTS (SELECT 1 FROM entry_infor ei "
                    f"WHERE ei.university_id = u.id AND ei.`{col}` IS NOT NULL)"
                )

        where_sql = " AND ".join(where_clauses)

        sql = text(f"""
            SELECT {_SCORE_JOIN_SELECT}
            FROM (
                SELECT u.id, u.rank_int, u.overall_score, u.name, u.city, u.country_id, u.logo
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                WHERE {where_sql}
                ORDER BY u.rank_int ASC, u.id ASC
                LIMIT 2000
            ) u
            {_SCORE_JOINS}
            ORDER BY u.rank_int ASC, u.id ASC
        """)

        rows = db.execute(sql, params).mappings().all()
        return [u.to_dict() for u in _build_uni_map(rows).values()]

    @staticmethod
    def get_university_by_id(db: Session, university_id: int) -> Optional[Dict[str, Any]]:
        sql = text(f"""
            SELECT {_SCORE_JOIN_SELECT}
            FROM (
                SELECT id, rank_int, overall_score, name, city, country_id, logo
                FROM universities WHERE id = :uni_id
            ) u
            {_SCORE_JOINS}
        """)
        rows = db.execute(sql, {"uni_id": university_id}).mappings().all()
        uni_map = _build_uni_map(rows)
        if not uni_map:
            return None
        uni = uni_map[university_id]
        return uni.to_dict()

    @staticmethod
    def _parse_score(value) -> Optional[float]:
        if value is None:
            return None
        try:
            cleaned = str(value).replace("+", "").strip()
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_entry_requirements(db: Session, university_id: int) -> Optional[Dict[str, Any]]:
        sql = text("""
            SELECT
                u.name    AS uni_name,
                u.rank_int AS uni_rank,
                e.degree_type,
                e.SAT  AS sat,
                e.GRE  AS gre,
                e.GMAT AS gmat,
                e.ACT  AS act,
                e.ATAR AS atar,
                e.GPA  AS gpa,
                e.TOEFL AS toefl,
                e.IELTS AS ielts
            FROM universities u
            LEFT JOIN entry_infor e ON u.id = e.university_id
            WHERE u.id = :uni_id
        """)
        results = db.execute(sql, {"uni_id": university_id}).mappings().all()

        if not results:
            return None

        first = dict(results[0])
        out: Dict[str, Any] = {
            "name": first["uni_name"],
            "rank": first["uni_rank"],
            "bachelor": None,
            "master": None,
        }

        for row in results:
            row = dict(row)
            degree_type = row.get("degree_type")
            if degree_type is None:
                continue
            req_data = {
                "sat":  UniversityModel._parse_score(row.get("sat")),
                "gre":  UniversityModel._parse_score(row.get("gre")),
                "gmat": UniversityModel._parse_score(row.get("gmat")),
                "act":  UniversityModel._parse_score(row.get("act")),
                "atar": UniversityModel._parse_score(row.get("atar")),
                "gpa":  UniversityModel._parse_score(row.get("gpa")),
                "toefl": UniversityModel._parse_score(row.get("toefl")),
                "ielts": UniversityModel._parse_score(row.get("ielts")),
            }
            if degree_type == 1:
                out["bachelor"] = req_data
            elif degree_type == 2:
                out["master"] = req_data

        return out

    @staticmethod
    def get_detail_information(db: Session, university_id: int) -> Optional[Dict[str, Any]]:
        sql = text("""
            SELECT
                u.name,
                COALESCE(d.fee, \\'\\')           AS fee,
                COALESCE(d.scholarship, 0)         AS scholarship,
                COALESCE(d.domestic, \\'\\')       AS domestic,
                COALESCE(d.international, \\'\\')  AS international,
                COALESCE(d.total_stu, \\'\\')      AS total_stu,
                COALESCE(d.ug_rate, \\'\\')        AS ug_rate,
                COALESCE(d.pg_rate, \\'\\')        AS pg_rate,
                COALESCE(d.inter_total, \\'\\')    AS inter_total,
                COALESCE(d.inter_ug_rate, \\'\\')  AS inter_ug_rate,
                COALESCE(d.inter_pg_rate, \\'\\')  AS inter_pg_rate
            FROM universities u
            LEFT JOIN detail_infors d ON u.id = d.university_id
            WHERE u.id = :uni_id
        """)
        row = db.execute(sql, {"uni_id": university_id}).mappings().first()
        if not row:
            return None
        return DetailInfor.from_dict(dict(row)).to_dict()

    @staticmethod
    def get_comparison_data(db: Session, university_ids: List[int]) -> List[Dict[str, Any]]:
        if not university_ids:
            return []
        placeholders = ", ".join(f":id_{i}" for i in range(len(university_ids)))
        params = {f"id_{i}": uid for i, uid in enumerate(university_ids)}
        sql = text(f"""
            SELECT
                u.id,
                u.name,
                COALESCE(d.fee, \\'\\')          AS fee,
                COALESCE(d.scholarship, 0)        AS scholarship,
                COALESCE(d.domestic, \\'\\')      AS domestic,
                COALESCE(d.international, \\'\\') AS international,
                COALESCE(d.total_stu, \\'\\')     AS total_stu,
                COALESCE(d.ug_rate, \\'\\')       AS ug_rate,
                COALESCE(d.pg_rate, \\'\\')       AS pg_rate,
                COALESCE(d.inter_total, \\'\\')   AS inter_total,
                COALESCE(d.inter_ug_rate, \\'\\') AS inter_ug_rate,
                COALESCE(d.inter_pg_rate, \\'\\') AS inter_pg_rate
            FROM universities u
            LEFT JOIN detail_infors d ON u.id = d.university_id
            WHERE u.id IN ({placeholders})
        """)
        rows = db.execute(sql, params).mappings().all()
        return [DetailInfor.from_dict(dict(r)).to_dict() for r in rows]

    @staticmethod
    def get_chart_data(db: Session, university_ids: List[int]) -> List[Dict[str, Any]]:
        if not university_ids:
            return []
        placeholders = ", ".join(f":id_{i}" for i in range(len(university_ids)))
        params = {f"id_{i}": uid for i, uid in enumerate(university_ids)}
        sql = text(f"""
            SELECT
                u.id, u.name, e.degree_type,
                e.SAT  AS sat,  e.GRE  AS gre,  e.GMAT AS gmat,
                e.ACT  AS act,  e.ATAR AS atar,  e.GPA  AS gpa,
                e.TOEFL AS toefl, e.IELTS AS ielts
            FROM universities u
            LEFT JOIN entry_infor e ON u.id = e.university_id
            WHERE u.id IN ({placeholders})
            ORDER BY u.id, e.degree_type
        """)
        rows = db.execute(sql, params).mappings().all()

        def _row_scores(row):
            return {
                k: UniversityModel._parse_score(row.get(k))
                for k in ("sat", "gre", "gmat", "act", "atar", "gpa", "toefl", "ielts")
            }

        uni_map: Dict[int, Dict] = {}
        for row in rows:
            row = dict(row)
            uid = row["id"]
            if uid not in uni_map:
                uni_map[uid] = {"id": uid, "name": row["name"], "bachelor": None, "master": None}
            dt = row.get("degree_type")
            if dt == 1:
                uni_map[uid]["bachelor"] = _row_scores(row)
            elif dt == 2:
                uni_map[uid]["master"] = _row_scores(row)

        return [uni_map[uid] for uid in university_ids if uid in uni_map]
'''

# ─────────────────────────────── write files ─────────────────────────────────
for filename, content in FILES.items():
    path = BASE / filename
    path.write_text(content, encoding="utf-8")
    print(f"  Written: {path}")

print("\nAll model files written successfully.")

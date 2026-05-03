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
from app.entities.enums import REGION_LABELS
from typing import Optional, Dict, Any, List


_SCORE_JOIN_SELECT = """
    u.id,
    u.rank_int,
    u.overall_score,
    u.name        AS university_name,
    u.city,
    c.region_id,
    u.country_id,
    u.path,
    c.name        AS country_name,
    u.logo,
    st.name       AS score_type,
    i.name        AS indicator_name,
    s.score
"""

_SCORE_JOINS = """
    LEFT JOIN countries   c  ON u.country_id      = c.id
    LEFT JOIN scores      s  ON u.id              = s.university_id
    LEFT JOIN indicators  i  ON i.id              = s.indicator_id
    LEFT JOIN score_types st ON st.id             = i.score_type_id
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
                region_id=row.get("region_id"),
                country_id=row.get("country_id"),
                path=row.get("path"),
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
                SELECT id, rank_int, overall_score, name, city, country_id, path, logo
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
    def get_regions(db: Session) -> List[dict]:
        from app.entities.country import Country
        used_ids = (
            db.query(Country.region_id)
            .filter(Country.region_id.isnot(None))
            .distinct()
            .all()
        )
        ids = sorted({row[0] for row in used_ids})
        return [{"id": rid, "name": REGION_LABELS[rid]} for rid in ids if rid in REGION_LABELS]

    @staticmethod
    def get_countries_by_region(db: Session, region_id: Optional[int] = None) -> List[Dict[str, Any]]:
        from app.entities.country import Country
        query = db.query(Country)
        if region_id is not None:
            query = query.filter(Country.region_id == region_id)
        results = query.order_by(Country.name).all()
        return [{"id": r.id, "name": r.name} for r in results]

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
        region_id: Optional[int] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        min_rank: Optional[int] = None,
        max_rank: Optional[int] = None,
        english_tests: Optional[List[str]] = None,
        academic_tests: Optional[List[str]] = None,
        min_international_pct: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        where_clauses = ["1=1"]
        params: Dict[str, Any] = {}

        if region_id is not None:
            where_clauses.append("c.region_id = :region_id")
            params["region_id"] = region_id
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

        # Map từ tên hiển thị → tên cột trong entry_infor (uppercase)
        TEST_COLUMN_MAP = {
            "IELTS": "IELTS",
            "TOEFL": "TOEFL",
            "SAT": "SAT",
            "GRE": "GRE",
            "GMAT": "GMAT",
            "ACT": "ACT",
            "ATAR": "ATAR",
            "GPA": "GPA",
        }
        all_tests = list(english_tests or []) + list(academic_tests or [])
        for test_name in all_tests:
            col = TEST_COLUMN_MAP.get(test_name)
            if col:
                where_clauses.append(
                    f"EXISTS (SELECT 1 FROM entry_infor ei "
                    f"WHERE ei.university_id = u.id AND ei.`{col}` IS NOT NULL)"
                )

        if min_international_pct is not None and min_international_pct > 0:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM detail_infors di "
                "WHERE di.university_id = u.id "
                "AND CAST(REPLACE(REPLACE(di.international, '%', ''), ' ', '') AS DECIMAL(5,2)) >= :min_intl_pct)"
            )
            params["min_intl_pct"] = min_international_pct

        where_sql = " AND ".join(where_clauses)

        sql = text(f"""
            SELECT {_SCORE_JOIN_SELECT}
            FROM (
                SELECT u.id, u.rank_int, u.overall_score, u.name, u.city, u.country_id, u.path, u.logo
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
                SELECT id, rank_int, overall_score, name, city, country_id, path, logo
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
    def get_scholarships(db: Session, university_id: int) -> List[Dict[str, Any]]:
        from app.entities.scholarship import Scholarship
        rows = db.query(Scholarship).filter(Scholarship.university_id == university_id).all()
        return [r.to_dict() for r in rows]

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
    def get_entry_requirements(db: Session, university_id: int, degree_type: int = None) -> Optional[Dict[str, Any]]:
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
                COALESCE(d.fee, \'\')           AS fee,
                COALESCE(d.scholarship, 0)         AS scholarship,
                COALESCE(d.domestic, \'\')       AS domestic,
                COALESCE(d.international, \'\')  AS international,
                COALESCE(d.total_stu, \'\')      AS total_stu,
                COALESCE(d.ug_rate, \'\')        AS ug_rate,
                COALESCE(d.pg_rate, \'\')        AS pg_rate,
                COALESCE(d.inter_total, \'\')    AS inter_total,
                COALESCE(d.inter_ug_rate, \'\')  AS inter_ug_rate,
                COALESCE(d.inter_pg_rate, \'\')  AS inter_pg_rate
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
                COALESCE(d.fee, \'\')          AS fee,
                COALESCE(d.scholarship, 0)        AS scholarship,
                COALESCE(d.domestic, \'\')      AS domestic,
                COALESCE(d.international, \'\') AS international,
                COALESCE(d.total_stu, \'\')     AS total_stu,
                COALESCE(d.ug_rate, \'\')       AS ug_rate,
                COALESCE(d.pg_rate, \'\')       AS pg_rate,
                COALESCE(d.inter_total, \'\')   AS inter_total,
                COALESCE(d.inter_ug_rate, \'\') AS inter_ug_rate,
                COALESCE(d.inter_pg_rate, \'\') AS inter_pg_rate
            FROM universities u
            LEFT JOIN detail_infors d ON u.id = d.university_id
            WHERE u.id IN ({placeholders})
        """)
        rows = db.execute(sql, params).mappings().all()
        result = []
        for r in rows:
            row_dict = dict(r)
            detail = DetailInfor.from_dict(row_dict).to_dict()
            detail['id'] = row_dict.get('id')
            detail['name'] = row_dict.get('name')
            result.append(detail)
        return result

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

    # ── indicator key → indicator_id (from DB) ───────────────────────────────
    _INDICATOR_MAP = {
        "academic_reputation":      76,
        "citations_per_faculty":    73,
        "intl_research_network":    15,
        "faculty_student_ratio":    36,
        "employer_reputation":      77,
        "employment_outcomes":      3819456,
        "intl_student_ratio":       14,
        "intl_faculty_ratio":       18,
        "intl_student_diversity":   3924415,
        "sustainability_score":     3897497,
    }

    @staticmethod
    def create_university(db: Session, data: dict) -> dict:
        """Insert university + detail_infor + entry_infor + scores rows."""
        # 1. universities
        uni = University(
            name=data.get("name", ""),
            city=data.get("city"),
            country_id=data.get("country_id") or None,
            logo=data.get("logo"),
            path=data.get("path"),
            rank_int=data.get("rank_int") or None,
            overall_score=data.get("overall_score") or None,
        )
        db.add(uni)
        db.flush()  # get uni.id without committing

        # 2. detail_infors
        detail = data.get("detail") or {}
        di = DetailInfor(
            university_id=uni.id,
            fee=str(detail.get("fee")) if detail.get("fee") not in (None, "") else None,
            scholarship=detail.get("scholarship"),
            domestic=str(detail.get("domestic")) if detail.get("domestic") not in (None, "") else None,
            international=str(detail.get("international")) if detail.get("international") not in (None, "") else None,
            english_test=detail.get("english_test"),
            academic_test=detail.get("academic_test"),
            total_stu=str(detail.get("total_stu")) if detail.get("total_stu") not in (None, "") else None,
            ug_rate=str(detail.get("ug_rate")) if detail.get("ug_rate") not in (None, "") else None,
            pg_rate=str(detail.get("pg_rate")) if detail.get("pg_rate") not in (None, "") else None,
            inter_total=str(detail.get("inter_total")) if detail.get("inter_total") not in (None, "") else None,
            inter_ug_rate=str(detail.get("inter_ug_rate")) if detail.get("inter_ug_rate") not in (None, "") else None,
            inter_pg_rate=str(detail.get("inter_pg_rate")) if detail.get("inter_pg_rate") not in (None, "") else None,
        )
        db.add(di)

        # 3. entry_infor (degree_type 1 & 2)
        entry = data.get("entry") or {}
        for deg_str, vals in entry.items():
            deg = int(deg_str)
            ei = EntryInfor(
                university_id=uni.id,
                degree_type=deg,
                sat=vals.get("SAT") or None,
                act=vals.get("ACT") or None,
                gre=vals.get("GRE") or None,
                gmat=vals.get("GMAT") or None,
                atar=vals.get("ATAR") or None,
                gpa=vals.get("GPA") or None,
                toefl=vals.get("TOEFL") or None,
                ielts=vals.get("IELTS") or None,
            )
            db.add(ei)

        # 4. scores — flat dict {indicator_key: {score, rank}}
        from app.entities.score import Score as ScoreEntity
        scores_flat = data.get("scores") or {}
        for key, val in scores_flat.items():
            ind_id = UniversityModel._INDICATOR_MAP.get(key)
            if ind_id is None:
                continue
            sc_val = val.get("score") if isinstance(val, dict) else None
            rk_val = val.get("rank")  if isinstance(val, dict) else None
            if sc_val in (None, "") and rk_val in (None, ""):
                continue
            sc = ScoreEntity(
                university_id=uni.id,
                indicator_id=ind_id,
                score=float(sc_val) if sc_val not in (None, "") else None,
                rank_int=int(rk_val) if rk_val not in (None, "") else None,
            )
            db.add(sc)

        db.commit()
        db.refresh(uni)
        return {"id": uni.id, "name": uni.name}

    @staticmethod
    def get_edit_data(db: Session, university_id: int) -> dict:
        """Return entry_requirements + edit_scores in the format expected by the edit form."""
        # Entry requirements — all degree types
        entry_sql = text("""
            SELECT degree_type, SAT, ACT, GRE, GMAT, ATAR, GPA, TOEFL, IELTS
            FROM entry_infor WHERE university_id = :uid
        """)
        entry_rows = db.execute(entry_sql, {"uid": university_id}).mappings().all()
        entry_requirements = [
            {
                "degree_type": r["degree_type"],
                "SAT":  r["SAT"],  "ACT":  r["ACT"],
                "GRE":  r["GRE"],  "GMAT": r["GMAT"],
                "ATAR": r["ATAR"], "GPA":  r["GPA"],
                "TOEFL": r["TOEFL"], "IELTS": r["IELTS"],
            }
            for r in entry_rows
        ]

        # Scores — reverse-map indicator_id → (cat_key, ind_key)
        reverse_map = {v: k for k, v in UniversityModel._INDICATOR_MAP.items()}
        cat_map = {
            "academic_reputation":    "research_discovery",
            "citations_per_faculty":  "research_discovery",
            "intl_research_network":  "research_discovery",
            "faculty_student_ratio":  "learning_experience",
            "employer_reputation":    "employability",
            "employment_outcomes":    "employability",
            "intl_student_ratio":     "global_engagement",
            "intl_faculty_ratio":     "global_engagement",
            "intl_student_diversity": "global_engagement",
            "sustainability_score":   "sustainability",
        }
        score_sql = text("""
            SELECT indicator_id, score, rank_int
            FROM scores WHERE university_id = :uid
        """)
        score_rows = db.execute(score_sql, {"uid": university_id}).mappings().all()
        edit_scores: Dict[str, Any] = {}
        for row in score_rows:
            ind_id  = row["indicator_id"]
            ind_key = reverse_map.get(ind_id)
            if not ind_key:
                continue
            cat_key = cat_map.get(ind_key)
            if not cat_key:
                continue
            edit_scores.setdefault(cat_key, {})[ind_key] = {
                "score": row["score"],
                "rank":  row["rank_int"],
            }

        return {"entry_requirements": entry_requirements, "edit_scores": edit_scores}

    @staticmethod
    def get_ranking_scores(db: Session, university_id: int) -> List[Dict[str, Any]]:
        """Return ranking scores grouped by score_type category, each with indicator name, score, rank_int."""
        sql = text("""
            SELECT
                st.name  AS category,
                i.name   AS indicator,
                s.score,
                s.rank_int
            FROM scores s
            JOIN indicators  i  ON i.id  = s.indicator_id
            JOIN score_types st ON st.id = i.score_type_id
            WHERE s.university_id = :uid
            ORDER BY st.id ASC, i.id ASC
        """)
        rows = db.execute(sql, {"uid": university_id}).mappings().all()

        categories: Dict[str, list] = {}
        cat_order: List[str] = []
        for row in rows:
            cat = row["category"]
            if cat not in categories:
                categories[cat] = []
                cat_order.append(cat)
            categories[cat].append({
                "name":  row["indicator"],
                "score": row["score"],
                "rank":  row["rank_int"],
            })

        return [{"category": cat, "indicators": categories[cat]} for cat in cat_order]

    @staticmethod
    def update_university(db: Session, university_id: int, data: dict) -> dict:
        """Update university + related rows."""
        uni = db.query(University).filter(University.id == university_id).first()
        if not uni:
            return None

        for field in ("name", "city", "country_id", "logo", "path", "rank_int", "overall_score"):
            if field in data and data[field] not in ("", None) or (field in data and data[field] == False):
                setattr(uni, field, data[field] or None if field != "name" else data[field])

        # detail_infors
        detail = data.get("detail") or {}
        if detail:
            di = db.query(DetailInfor).filter(DetailInfor.university_id == university_id).first()
            if not di:
                di = DetailInfor(university_id=university_id)
                db.add(di)
            for field in ("fee", "scholarship", "domestic", "international", "english_test",
                          "academic_test", "total_stu", "ug_rate", "pg_rate",
                          "inter_total", "inter_ug_rate", "inter_pg_rate"):
                val = detail.get(field)
                if val not in (None, ""):
                    setattr(di, field, str(val) if field != "scholarship" else val)

        # entry_infor
        entry = data.get("entry") or {}
        for deg_str, vals in entry.items():
            deg = int(deg_str)
            ei = db.query(EntryInfor).filter(
                EntryInfor.university_id == university_id,
                EntryInfor.degree_type == deg
            ).first()
            if not ei:
                ei = EntryInfor(university_id=university_id, degree_type=deg)
                db.add(ei)
            for attr in ("SAT", "ACT", "GRE", "GMAT", "ATAR", "GPA", "TOEFL", "IELTS"):
                val = vals.get(attr)
                setattr(ei, attr.lower(), val or None)

        # scores
        from app.entities.score import Score as ScoreEntity
        scores_flat = data.get("scores") or {}
        for key, val in scores_flat.items():
            ind_id = UniversityModel._INDICATOR_MAP.get(key)
            if ind_id is None:
                continue
            sc_val = val.get("score") if isinstance(val, dict) else None
            rk_val = val.get("rank")  if isinstance(val, dict) else None
            sc = db.query(ScoreEntity).filter(
                ScoreEntity.university_id == university_id,
                ScoreEntity.indicator_id == ind_id
            ).first()
            if sc_val in (None, "") and rk_val in (None, ""):
                continue
            if not sc:
                sc = ScoreEntity(university_id=university_id, indicator_id=ind_id)
                db.add(sc)
            sc.score = float(sc_val) if sc_val not in (None, "") else None
            sc.rank_int = int(rk_val) if rk_val not in (None, "") else None

        db.commit()
        db.refresh(uni)
        return {"id": uni.id, "name": uni.name}

"""
University Model - Data access layer for universities.
Adapted from existing models/UniversityModel.py
"""
from app.database import execute_query
from typing import Optional, Dict, Any, List, Tuple


class UniversityModel:
    """University data access layer"""

    @staticmethod
    def get_all_universities(limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all universities with their scores.

        Args:
            limit: Maximum number of results (default: 50)

        Returns:
            List of universities with scores
        """
        try:
            sql = """
                SELECT 
                    u.id,
                    u.rank_int,
                    u.overall_score,
                    u.name AS university_name,
                    u.city,
                    c.name AS country_name,
                    u.logo,
                    st.name AS score_type,
                    i.name AS indicator_name,
                    s.score
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                LEFT JOIN scores s ON u.id = s.university_id
                LEFT JOIN score_types st ON s.score_type_id = st.id
                LEFT JOIN indicators i ON i.id = s.indicator_id
                ORDER BY u.rank_int ASC, u.id ASC
                LIMIT %s
            """
            results = execute_query(sql, (limit,), fetch=True)

            # Group results by university
            universities_map = {}
            for row in results:
                uni_id = row['id']
                if uni_id not in universities_map:
                    universities_map[uni_id] = {
                        'id': row['id'],
                        'rank': row['rank_int'],
                        'overall_score': row['overall_score'] or 0.0,
                        'name': row['university_name'],
                        'city': row['city'],
                        'country': row['country_name'],
                        'logo': row['logo'],
                        'scores': {}
                    }

                # Add score if available
                if row['score_type'] and row['indicator_name']:
                    if row['score_type'] not in universities_map[uni_id]['scores']:
                        universities_map[uni_id]['scores'][row['score_type']] = {}
                    universities_map[uni_id]['scores'][row['score_type']][row['indicator_name']] = row['score']

            return list(universities_map.values())
        except Exception as e:
            print(f"Error getting all universities: {e}")
            return []

    @staticmethod
    def search_universities_by_name(name: str) -> List[Dict[str, Any]]:
        """
        Search universities by name.

        Args:
            name: University name (partial match)

        Returns:
            List of matching universities
        """
        try:
            # Build search pattern
            search_pattern = f"%{name}%"

            sql = """
                SELECT 
                    u.id,
                    u.rank_int,
                    u.overall_score,
                    u.name AS university_name,
                    u.city,
                    c.name AS country_name,
                    u.logo,
                    st.name AS score_type,
                    i.name AS indicator_name,
                    s.score
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                LEFT JOIN scores s ON u.id = s.university_id
                LEFT JOIN score_types st ON s.score_type_id = st.id
                LEFT JOIN indicators i ON i.id = s.indicator_id
                WHERE u.name LIKE %s
                ORDER BY u.rank_int ASC
                LIMIT 50
            """
            results = execute_query(sql, (search_pattern,), fetch=True)

            # Group results by university
            universities_map = {}
            for row in results:
                uni_id = row['id']
                if uni_id not in universities_map:
                    universities_map[uni_id] = {
                        'id': row['id'],
                        'rank': row['rank_int'],
                        'overall_score': row['overall_score'] or 0.0,
                        'name': row['university_name'],
                        'city': row['city'],
                        'country': row['country_name'],
                        'logo': row['logo'],
                        'scores': {}
                    }

                if row['score_type'] and row['indicator_name']:
                    if row['score_type'] not in universities_map[uni_id]['scores']:
                        universities_map[uni_id]['scores'][row['score_type']] = {}
                    universities_map[uni_id]['scores'][row['score_type']][row['indicator_name']] = row['score']

            return list(universities_map.values())
        except Exception as e:
            print(f"Error searching universities: {e}")
            return []

    @staticmethod
    def filter_universities(region: Optional[str] = None, country: Optional[str] = None, 
                           min_rank: Optional[int] = None, max_rank: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Filter universities by criteria.

        Args:
            region: Region filter
            country: Country filter
            min_rank: Minimum ranking
            max_rank: Maximum ranking

        Returns:
            List of filtered universities
        """
        try:
            sql = """
                SELECT 
                    u.id,
                    u.rank_int,
                    u.overall_score,
                    u.name AS university_name,
                    u.city,
                    c.name AS country_name,
                    u.logo,
                    st.name AS score_type,
                    i.name AS indicator_name,
                    s.score
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                LEFT JOIN scores s ON u.id = s.university_id
                LEFT JOIN score_types st ON s.score_type_id = st.id
                LEFT JOIN indicators i ON i.id = s.indicator_id
                WHERE 1=1
            """
            params = []

            if region:
                sql += " AND u.region LIKE %s"
                params.append(f"%{region}%")
            if country:
                sql += " AND c.name LIKE %s"
                params.append(f"%{country}%")
            if min_rank is not None:
                sql += " AND u.rank_int >= %s"
                params.append(min_rank)
            if max_rank is not None:
                sql += " AND u.rank_int <= %s"
                params.append(max_rank)

            sql += " ORDER BY u.rank_int ASC LIMIT 50"

            results = execute_query(sql, tuple(params), fetch=True)

            # Group results by university
            universities_map = {}
            for row in results:
                uni_id = row['id']
                if uni_id not in universities_map:
                    universities_map[uni_id] = {
                        'id': row['id'],
                        'rank': row['rank_int'],
                        'overall_score': row['overall_score'] or 0.0,
                        'name': row['university_name'],
                        'city': row['city'],
                        'country': row['country_name'],
                        'logo': row['logo'],
                        'scores': {}
                    }

                if row['score_type'] and row['indicator_name']:
                    if row['score_type'] not in universities_map[uni_id]['scores']:
                        universities_map[uni_id]['scores'][row['score_type']] = {}
                    universities_map[uni_id]['scores'][row['score_type']][row['indicator_name']] = row['score']

            return list(universities_map.values())
        except Exception as e:
            print(f"Error filtering universities: {e}")
            return []

    @staticmethod
    def get_university_by_id(university_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific university by ID.

        Args:
            university_id: University ID

        Returns:
            University dict if found, None otherwise
        """
        try:
            sql = """
                SELECT 
                    u.id,
                    u.rank_int,
                    u.overall_score,
                    u.name AS university_name,
                    u.city,
                    c.name AS country_name,
                    u.logo,
                    u.path,
                    st.name AS score_type,
                    i.name AS indicator_name,
                    s.score
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                LEFT JOIN scores s ON u.id = s.university_id
                LEFT JOIN score_types st ON s.score_type_id = st.id
                LEFT JOIN indicators i ON i.id = s.indicator_id
                WHERE u.id = %s
            """
            results = execute_query(sql, (university_id,), fetch=True)

            if not results:
                return None

            # Build university object from first row
            first_row = results[0]
            university = {
                'id': first_row['id'],
                'rank': first_row['rank_int'],
                'overall_score': first_row['overall_score'] or 0.0,
                'name': first_row['university_name'],
                'city': first_row['city'],
                'country': first_row['country_name'],
                'logo': first_row['logo'],
                'path': first_row['path'],
                'scores': {}
            }

            # Add all scores
            for row in results:
                if row['score_type'] and row['indicator_name']:
                    if row['score_type'] not in university['scores']:
                        university['scores'][row['score_type']] = {}
                    university['scores'][row['score_type']][row['indicator_name']] = row['score']

            return university
        except Exception as e:
            print(f"Error getting university: {e}")
            return None

    @staticmethod
    def get_entry_requirements(university_id: int, degree_type: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get entry requirements for a university.

        Args:
            university_id: University ID
            degree_type: 1 for bachelor, 2 for master

        Returns:
            Entry requirements dict
        """
        try:
            sql = """
                SELECT 
                    u.name,
                    CONCAT(COALESCE(c.name, ''), ',', COALESCE(u.city, '')) AS address,
                    u.rank_int as rank,
                    COALESCE(e.SAT, 'N/A') AS SAT,
                    COALESCE(e.GRE, 'N/A') AS GRE,
                    COALESCE(e.GMAT, 'N/A') AS GMAT,
                    COALESCE(e.ACT, 'N/A') AS ACT,
                    COALESCE(e.ATAR, 'N/A') AS ATAR,
                    COALESCE(e.GPA, 'N/A') AS GPA,
                    COALESCE(e.TOEFL, 'N/A') AS TOEFL,
                    COALESCE(e.IELTS, 'N/A') AS IELTS
                FROM universities u
                LEFT JOIN countries c ON u.country_id = c.id
                LEFT JOIN entry_infor e ON u.id = e.university_id AND e.degree_type = %s
                WHERE u.id = %s
            """
            result = execute_query(sql, (degree_type, university_id), fetch=True, fetch_one=True)

            if not result:
                return None

            return {
                'name': result['name'],
                'address': result['address'],
                'rank': result['rank'],
                'SAT': result['SAT'],
                'GRE': result['GRE'],
                'GMAT': result['GMAT'],
                'ACT': result['ACT'],
                'ATAR': result['ATAR'],
                'GPA': result['GPA'],
                'TOEFL': result['TOEFL'],
                'IELTS': result['IELTS']
            }
        except Exception as e:
            print(f"Error getting entry requirements: {e}")
            return None

    @staticmethod
    def get_detail_information(university_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detail information about a university.

        Args:
            university_id: University ID

        Returns:
            Detail information dict
        """
        try:
            sql = """
                SELECT
                    u.name,
                    COALESCE(d.fee, '') AS fee,
                    COALESCE(d.scholarship, 0) AS scholarship,
                    COALESCE(d.domestic, '') AS domestic,
                    COALESCE(d.international, '') AS international,
                    COALESCE(d.total_stu, '') AS total_stu,
                    COALESCE(d.ug_rate, '') AS ug_rate,
                    COALESCE(d.pg_rate, '') AS pg_rate,
                    COALESCE(d.inter_total, '') AS inter_total,
                    COALESCE(d.inter_ug_rate, '') AS inter_ug_rate,
                    COALESCE(d.inter_pg_rate, '') AS inter_pg_rate
                FROM universities u
                LEFT JOIN detail_infors d ON u.id = d.university_id
                WHERE u.id = %s
            """
            result = execute_query(sql, (university_id,), fetch=True, fetch_one=True)

            if not result:
                return None

            return dict(result)
        except Exception as e:
            print(f"Error getting detail information: {e}")
            return None

    @staticmethod
    def get_comparison_data(university_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get data for comparing multiple universities.

        Args:
            university_ids: List of university IDs to compare

        Returns:
            List of comparison data
        """
        try:
            if not university_ids:
                return []

            placeholders = ",".join(["%s"] * len(university_ids))
            sql = f"""
                SELECT
                    u.name,
                    COALESCE(d.fee, '') AS fee,
                    COALESCE(d.scholarship, 0) AS scholarship,
                    COALESCE(d.domestic, '') AS domestic,
                    COALESCE(d.international, '') AS international,
                    COALESCE(d.total_stu, '') AS total_stu,
                    COALESCE(d.ug_rate, '') AS ug_rate,
                    COALESCE(d.pg_rate, '') AS pg_rate,
                    COALESCE(d.inter_total, '') AS inter_total,
                    COALESCE(d.inter_ug_rate, '') AS inter_ug_rate,
                    COALESCE(d.inter_pg_rate, '') AS inter_pg_rate
                FROM universities u
                LEFT JOIN detail_infors d ON u.id = d.university_id
                WHERE u.id IN ({placeholders})
            """
            results = execute_query(sql, tuple(university_ids), fetch=True)
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting comparison data: {e}")
            return []

    @staticmethod
    def get_chart_data(university_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get entry requirement data for creating comparison charts.

        Args:
            university_ids: List of university IDs

        Returns:
            List of chart data
        """
        try:
            if not university_ids:
                return []

            placeholders = ",".join(["%s"] * len(university_ids))
            sql = f"""
                SELECT 
                    u.name,
                    COALESCE(e.SAT, 0) AS sat,
                    COALESCE(e.GRE, 0) AS gre,
                    COALESCE(e.GMAT, 0) AS gmat,
                    COALESCE(e.ACT, 0) AS act,
                    COALESCE(e.ATAR, 0) AS atar,
                    COALESCE(e.GPA, 0) AS gpa,
                    COALESCE(e.TOEFL, 0) AS toefl,
                    COALESCE(e.IELTS, 0) AS ielts
                FROM universities u
                LEFT JOIN entry_infor e ON u.id = e.university_id AND e.degree_type = 1
                WHERE u.id IN ({placeholders})
            """
            results = execute_query(sql, tuple(university_ids), fetch=True)
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting chart data: {e}")
            return []

"""
Country Model - Data access layer for countries table.
Adapted from existing models/CountryModel.py
"""
from app.database import execute_query
from typing import Optional, Dict, Any, List


class CountryModel:
    """Country data access layer"""

    @staticmethod
    def get_by_id(country_id: int) -> Optional[Dict[str, Any]]:
        """
        Get country by ID.

        Args:
            country_id: Country ID

        Returns:
            Country dict if found, None otherwise
        """
        try:
            sql = "SELECT id, name FROM countries WHERE id = %s"
            result = execute_query(sql, (country_id,), fetch=True, fetch_one=True)
            return result
        except Exception as e:
            print(f"Error getting country: {e}")
            return None

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        Get country by name (case-insensitive).

        Args:
            name: Country name

        Returns:
            Country dict if found, None otherwise
        """
        try:
            sql = "SELECT id, name FROM countries WHERE LOWER(name) = LOWER(%s)"
            result = execute_query(sql, (name,), fetch=True, fetch_one=True)
            return result
        except Exception as e:
            print(f"Error getting country by name: {e}")
            return None

    @staticmethod
    def search_by_name(name: str) -> List[Dict[str, Any]]:
        """
        Search countries by name (partial match).

        Args:
            name: Country name or part of it

        Returns:
            List of matching countries
        """
        try:
            search_pattern = f"%{name}%"
            sql = "SELECT id, name FROM countries WHERE LOWER(name) LIKE LOWER(%s) ORDER BY name ASC LIMIT 50"
            results = execute_query(sql, (search_pattern,), fetch=True)
            return results or []
        except Exception as e:
            print(f"Error searching countries: {e}")
            return []

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """
        Get all countries.

        Returns:
            List of all countries sorted by name
        """
        try:
            sql = "SELECT id, name FROM countries ORDER BY name ASC"
            results = execute_query(sql, fetch=True)
            return results or []
        except Exception as e:
            print(f"Error getting all countries: {e}")
            return []

    @staticmethod
    def get_id_by_name(name: str) -> Optional[int]:
        """
        Get country ID by name (case-insensitive).
        Backward compatible with old model.

        Args:
            name: Country name

        Returns:
            Country ID if found, None otherwise
        """
        try:
            country = CountryModel.get_by_name(name)
            return country['id'] if country else None
        except Exception as e:
            print(f"Error getting country ID: {e}")
            return None

    @staticmethod
    def get_name_by_id(country_id: int) -> Optional[str]:
        """
        Get country name by ID.
        Backward compatible with old model.

        Args:
            country_id: Country ID

        Returns:
            Country name if found, None otherwise
        """
        try:
            country = CountryModel.get_by_id(country_id)
            return country['name'] if country else None
        except Exception as e:
            print(f"Error getting country name: {e}")
            return None

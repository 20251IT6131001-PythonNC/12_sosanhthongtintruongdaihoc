import mysql.connector
from mysql.connector import Error
from app.config import settings


def get_db_connection():
    """
    Create and return a database connection.
    Based on the existing db.py logic.
    """
    try:
        connection = mysql.connector.connect(
            host=settings.DATABASE_HOST,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            database=settings.DATABASE_NAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise


def execute_query(query, params=None, fetch=False, fetch_one=False):
    """
    Execute a database query.

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch: Whether to fetch results (SELECT queries)
        fetch_one: Whether to fetch only one result

    Returns:
        For SELECT queries: list of results or single result if fetch_one=True
        For INSERT/UPDATE/DELETE: lastrowid or rowcount
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())

        if fetch:
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    finally:
        cursor.close()
        connection.close()

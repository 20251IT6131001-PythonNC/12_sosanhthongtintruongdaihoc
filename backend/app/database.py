import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator
from app.config import settings


# ── SQLAlchemy 2.0 setup ──────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""
    pass


# Use URL.create() so special characters in password (e.g. @, #) are handled correctly
DATABASE_URL = URL.create(
    drivername="mysql+mysqlconnector",
    username=settings.DATABASE_USER,
    password=settings.DATABASE_PASSWORD,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    database=settings.DATABASE_NAME,
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Legacy helpers (kept for chatbot_engine.py backward compat) ───────────────

def get_db_connection():
    """Create and return a raw mysql.connector connection."""
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
    Execute a raw SQL query via mysql.connector.
    Kept for backward compatibility with chatbot_engine and other legacy callers.
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())

        if fetch:
            return cursor.fetchone() if fetch_one else cursor.fetchall()
        else:
            connection.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    finally:
        cursor.close()
        connection.close()

"""Application configuration.

DATABASE_URL precedence:
  1. DATABASE_URL env var (e.g. Postgres on Render).
  2. SQLite file at SQLITE_PATH (defaults to /var/data/fto.db on Render
     when a persistent disk is mounted, or instance/fto.db locally).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _resolve_database_uri() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Render/Heroku give postgres:// but SQLAlchemy 2.x wants postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url

    sqlite_path = os.environ.get("SQLITE_PATH")
    if sqlite_path:
        return f"sqlite:///{sqlite_path}"

    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    return f"sqlite:///{instance_dir / 'fto.db'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None  # don't expire CSRF tokens during long DOR entry
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _ensure_database_exists(database_url: str) -> str:
    if not settings.auto_create_database:
        return database_url

    url = make_url(database_url)
    if url.get_backend_name() != "mysql":
        return database_url

    database_name = url.database
    if not database_name:
        raise RuntimeError("MYSQL_DATABASE is missing from the database configuration.")

    server_url = url.set(database=None)
    server_engine = create_engine(server_url, pool_pre_ping=True, pool_recycle=3600)
    try:
        with server_engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        server_engine.dispose()

    return database_url


database_url = _ensure_database_exists(settings.resolved_database_url)
engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _use_pymysql_driver(database_url: str) -> str:
    url = make_url(database_url)
    if url.get_backend_name() == "mysql" and url.drivername == "mysql":
        return str(url.set(drivername="mysql+pymysql"))
    return database_url


DATABASE_URL = _use_pymysql_driver(settings.resolved_database_url)
print("Using DB:", DATABASE_URL)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

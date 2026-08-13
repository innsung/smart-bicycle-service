"""DB Engine, Session, Base와 FastAPI DB 의존성을 정의합니다."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


engine_options = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 SQLAlchemy 모델이 상속하는 부모 클래스."""


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB Session을 만들고 응답 후 안전하게 닫습니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

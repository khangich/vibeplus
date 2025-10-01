from collections.abc import Generator
from contextlib import contextmanager

from redis import Redis
from rq import Queue
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

_settings = get_settings()
_engine = create_engine(_settings.database_url, echo=False, connect_args={"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {})


def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(_engine)
    try:
        yield session
    finally:
        session.close()


def get_redis() -> Redis:
    return Redis.from_url(_settings.redis_url, decode_responses=True)


def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=get_redis())

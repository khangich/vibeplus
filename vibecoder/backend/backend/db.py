from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

from redis import Redis
from rq import Queue
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

_settings = get_settings()
_engine: Optional[Engine] = None
_engine_error: Optional[Exception] = None


def _engine_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _get_engine() -> Engine:
    global _engine, _engine_error
    if _engine is not None:
        return _engine
    if _engine_error is not None:
        raise RuntimeError("Database engine is unavailable") from _engine_error
    try:
        _engine = create_engine(
            _settings.database_url,
            echo=False,
            connect_args=_engine_connect_args(_settings.database_url),
        )
        return _engine
    except Exception as exc:  # pragma: no cover - defensive guard for local dev
        _engine_error = exc
        raise


def init_db() -> None:
    SQLModel.metadata.create_all(_get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    engine = _get_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_redis() -> Redis:
    # RQ stores job payloads as pickled bytes, so we must keep Redis responses
    # binary; enabling response decoding breaks job deserialization.
    return Redis.from_url(_settings.redis_url, decode_responses=False)


def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=get_redis())

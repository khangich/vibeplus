from __future__ import annotations

from datetime import datetime, timedelta

from redis import Redis

from .config import get_settings


def _bucket_key(user_id: str) -> str:
    return f"rl:{user_id}"


def is_rate_limited(redis: Redis, user_id: str) -> bool:
    settings = get_settings()
    capacity = settings.rate_limit_capacity
    refill_seconds = settings.rate_limit_refill_seconds
    if capacity <= 0:
        # TODO: should this be True?
        return False
    key = _bucket_key(user_id)
    tokens = redis.get(key)
    if tokens is None:
        expire_at_midnight(redis, key)
        redis.set(key, max(capacity - 1, 0), ex=refill_seconds)
        return False
    remaining = int(tokens)
    if remaining <= 0:
        return True
    redis.decr(key)
    return False


def expire_at_midnight(redis: Redis, key: str) -> None:
    now = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    ttl = int((tomorrow - now).total_seconds())
    redis.expire(key, ttl)

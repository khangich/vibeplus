from __future__ import annotations

from datetime import datetime, timedelta

from redis import Redis

CAPACITY = 20
REFILL_SECONDS = 24 * 60 * 60


def _bucket_key(user_id: str) -> str:
    return f"rl:{user_id}"


def is_rate_limited(redis: Redis, user_id: str) -> bool:
    key = _bucket_key(user_id)
    tokens = redis.get(key)
    if tokens is None:
        expire_at_midnight(redis, key)
        redis.set(key, CAPACITY - 1, ex=REFILL_SECONDS)
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

# worker/redis_client.py
import os
import redis

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # Upstash commonly uses TLS rediss://
    if url.startswith("rediss://"):
        return redis.Redis.from_url(url, ssl_cert_reqs=None)
    return redis.Redis.from_url(url)

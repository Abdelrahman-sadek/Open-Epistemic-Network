from __future__ import annotations

import os

import redis


def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_redis_client() -> redis.Redis:
    """
    Simple process-wide Redis client factory for queues and caching.
    """
    global _REDIS_CLIENT  # type: ignore[annotation-unchecked]
    try:
        return _REDIS_CLIENT
    except NameError:
        _REDIS_CLIENT = redis.from_url(get_redis_url())
        return _REDIS_CLIENT


"""Best-effort Redis cache with versioned namespaces.

Invalidation model: every namespace ("pois", ...) has a version counter.
Writers bump the version; readers include it in the key, so stale entries
simply expire via TTL instead of being deleted one by one. All operations
degrade to a no-op if Redis is unavailable — caching must never break reads.
"""

import asyncio
import hashlib
import json

import redis.asyncio as aioredis
from django.conf import settings

# Keyed by event loop: async redis connections are loop-bound, and the test
# suite spins up a fresh loop per TestClient. In production this holds one entry.
_clients: dict[int, aioredis.Redis] = {}


def client() -> aioredis.Redis:
    key = id(asyncio.get_running_loop())
    if key not in _clients:
        _clients[key] = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _clients[key]


def _prefix() -> str:
    # Include the DB name so pytest's test_* database never shares keys with dev.
    return f"rh:{settings.DATABASES['default']['NAME']}"


def _entry_key(namespace: str, version: int, params: dict) -> str:
    digest = hashlib.sha1(
        json.dumps(params, sort_keys=True, default=str).encode()
    ).hexdigest()
    return f"{_prefix()}:{namespace}:v{version}:{digest}"


async def get_cached(namespace: str, params: dict):
    try:
        r = client()
        version = int(await r.get(f"{_prefix()}:{namespace}:ver") or 0)
        raw = await r.get(_entry_key(namespace, version, params))
        return json.loads(raw) if raw else None
    except (aioredis.RedisError, OSError):
        return None


async def set_cached(namespace: str, params: dict, value, ttl: int | None = None) -> None:
    try:
        r = client()
        version = int(await r.get(f"{_prefix()}:{namespace}:ver") or 0)
        await r.set(
            _entry_key(namespace, version, params),
            json.dumps(value, default=str),
            ex=ttl or settings.POI_LIST_CACHE_TTL,
        )
    except (aioredis.RedisError, OSError):
        pass


async def bump_version(namespace: str) -> None:
    try:
        await client().incr(f"{_prefix()}:{namespace}:ver")
    except (aioredis.RedisError, OSError):
        pass

from __future__ import annotations
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional
import diskcache
from backend.config import get_settings

logger = logging.getLogger(__name__)
_cache: Optional[diskcache.Cache] = None


def get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        settings = get_settings()
        path = Path(settings.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        _cache = diskcache.Cache(str(path), size_limit=512 * 1024 * 1024)
    return _cache


def make_key(namespace: str, **kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{namespace}:{digest}"


def cget(key: str) -> Optional[Any]:
    try:
        return get_cache().get(key)
    except Exception as e:
        logger.warning("Cache read error: %s", e)
        return None


def cset(key: str, value: Any, ttl: Optional[int] = None) -> None:
    settings = get_settings()
    try:
        get_cache().set(key, value, expire=ttl or settings.cache_ttl_seconds)
    except Exception as e:
        logger.warning("Cache write error: %s", e)


def cdel_namespace(prefix: str) -> int:
    cache = get_cache()
    deleted = 0
    for key in list(cache.iterkeys()):
        if isinstance(key, str) and key.startswith(prefix):
            cache.delete(key)
            deleted += 1
    return deleted


def cache_info() -> dict:
    c = get_cache()
    return {"items": len(c), "size_mb": round(c.volume() / 1024 / 1024, 2), "dir": str(c.directory)}
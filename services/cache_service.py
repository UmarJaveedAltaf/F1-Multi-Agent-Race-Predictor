from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from diskcache import Cache
from config.settings import settings

@dataclass
class CacheService:
    cache_dir: str = str(settings.CACHE_DIR)

    def __post_init__(self):
        self._cache = Cache(self.cache_dir)

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key, default=None)

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._cache.set(key, value, expire=ttl)

    def close(self) -> None:
        self._cache.close()

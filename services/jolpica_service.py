from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time
import requests

from config.settings import settings
from services.cache_service import CacheService


@dataclass
class JolpicaService:
    cache: CacheService
    timeout: int = 20
    max_retries: int = 3

    def _request_json(self, url: str, params: Optional[dict] = None) -> Dict[str, Any]:
        last_err = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    time.sleep(0.6 * attempt)
                    continue

                response.raise_for_status()
                return response.json()

            except Exception as e:
                last_err = e
                time.sleep(0.4 * attempt)

        raise RuntimeError(f"Jolpica request failed: {last_err}")

    def get(self, path: str, params: Optional[dict] = None, ttl: int = None) -> Dict[str, Any]:
        ttl = settings.TTL_MED if ttl is None else ttl
        path = path if path.startswith("/") else f"/{path}"
        url = f"{settings.JOLPICA_BASE}{path}"

        cache_key = f"jolpica::{url}::{params}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._request_json(url, params=params)
        self.cache.set(cache_key, data, ttl=ttl)
        return data

    # -------- Convenience endpoints -------- #

    def seasons(self, limit: int = 100) -> Dict[str, Any]:
        return self.get("/seasons.json", params={"limit": limit}, ttl=settings.TTL_LONG)

    def races(self, season: int, limit: int = 100) -> Dict[str, Any]:
        return self.get(f"/{season}/races.json", params={"limit": limit}, ttl=settings.TTL_LONG)

    def results(self, season: int, round_no: int, limit: int = 100) -> Dict[str, Any]:
        return self.get(
            f"/{season}/{round_no}/results.json",
            params={"limit": limit},
            ttl=settings.TTL_LONG,
        )

    def driver_standings(self, season: int) -> Dict[str, Any]:
        return self.get(f"/{season}/driverstandings.json", ttl=settings.TTL_MED)

    def constructor_standings(self, season: int) -> Dict[str, Any]:
        return self.get(f"/{season}/constructorstandings.json", ttl=settings.TTL_MED)

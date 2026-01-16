from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import fastf1
from fastf1.core import Session

from config.settings import settings

@dataclass
class FastF1Service:
    cache_dir: Path = settings.CACHE_DIR / "fastf1"

    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Enable FastF1's built-in cache to reduce repeated downloads
        fastf1.Cache.enable_cache(str(self.cache_dir))

    def get_session(self, year: int, gp: str | int, session_name: str) -> Session:
        """
        gp can be round number (int) or GP name (str), ex: 2024, 1, "R"
        session_name: "FP1","FP2","FP3","Q","SQ","SS","R"
        """
        ses = fastf1.get_session(year, gp, session_name)
        ses.load(weather=True, messages=False)  # weather is useful for prediction
        return ses

    def get_race(self, year: int, gp: str | int) -> Session:
        return self.get_session(year, gp, "R")

    def get_qualifying(self, year: int, gp: str | int) -> Session:
        return self.get_session(year, gp, "Q")

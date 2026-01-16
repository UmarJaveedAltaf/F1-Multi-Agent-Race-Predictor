from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    CACHE_DIR: Path = PROJECT_ROOT / "data" / "cache"

    JOLPICA_BASE: str = os.getenv(
        "JOLPICA_BASE",
        "https://api.jolpi.ca/ergast/f1"
    )

    TTL_SHORT: int = int(os.getenv("TTL_SHORT", "3600"))       # 1 hour
    TTL_MED: int = int(os.getenv("TTL_MED", "21600"))         # 6 hours
    TTL_LONG: int = int(os.getenv("TTL_LONG", "604800"))      # 7 days


# ✅ THIS LINE IS CRITICAL
settings = Settings()

# Ensure cache dir exists
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)

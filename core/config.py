import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    base_url: str
    browser: str
    timeout_ms: int

    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv("SB_BASE_URL", "https://s-b-1.ru").rstrip("/"),
            browser=os.getenv("SB_BROWSER", "chromium"),
            timeout_ms=int(os.getenv("SB_TIMEOUT_MS", "15000")),
        )

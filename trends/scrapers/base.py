"""
Base utilities shared by all scrapers.
Standardized output format + helpers.
"""

import time
import hashlib
import requests
from datetime import datetime, timezone

# Shared session with sane defaults
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
})


def get_session() -> requests.Session:
    return _session


def make_item(
    source: str,
    title: str,
    url: str,
    score: float = 0.0,
    velocity: float = 0.0,
    category: str = "general",
    extra: dict = None,
) -> dict:
    """Create a standardized trend item."""
    now = datetime.now(timezone.utc).isoformat()
    item_id = hashlib.md5(f"{source}:{url}".encode()).hexdigest()[:12]
    return {
        "id": item_id,
        "source": source,
        "title": title.strip(),
        "url": url.strip(),
        "score": round(score, 2),
        "velocity": round(velocity, 2),
        "category": category,
        "timestamp": now,
        "extra": extra or {},
    }


def safe_get(url: str, timeout: int = 15, **kwargs):
    """GET with retries and error swallowing."""
    for attempt in range(3):
        try:
            resp = _session.get(url, timeout=timeout, **kwargs)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  [rate-limited] {url} — waiting {wait}s")
                time.sleep(wait)
                continue
            print(f"  [http {resp.status_code}] {url}")
            return None
        except requests.RequestException as e:
            print(f"  [error] {url} — {e}")
            if attempt < 2:
                time.sleep(1)
    return None

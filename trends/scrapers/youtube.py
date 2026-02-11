"""
YouTube Trending Scraper
Uses Invidious public API only (no key). YouTube's trending RSS returns 400.
We request default trending only (no category) to avoid 401/403 on instances.
"""

from .base import make_item, safe_get

try:
    from config import INVIDIOUS_INSTANCES
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import INVIDIOUS_INSTANCES


def _fetch_invidious_trending(instance: str) -> list[dict]:
    """Fetch default trending from one Invidious instance. No category = fewer 401s."""
    url = f"{instance}/api/v1/trending"
    resp = safe_get(url, params={}, timeout=12)
    if not resp:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    items = []
    for video in data[:30]:
        vid_id = video.get("videoId", "")
        title = video.get("title", "")
        views = video.get("viewCount", 0)
        published = video.get("published", 0)
        author = video.get("author", "")
        length = video.get("lengthSeconds", 0)
        items.append(make_item(
            source="youtube",
            title=title,
            url=f"https://www.youtube.com/watch?v={vid_id}",
            score=views / 1_000_000 if views else 0.5,
            category="trending",
            extra={
                "views": views,
                "author": author,
                "length_seconds": length,
                "published": published,
                "video_id": vid_id,
            },
        ))
    return items


def scrape() -> list[dict]:
    """Try each Invidious instance in order until one returns trending data."""
    print("[youtube] Scraping Invidious trending (default only)...")
    for i, instance in enumerate(INVIDIOUS_INSTANCES):
        print(f"  Trying {instance}...")
        items = _fetch_invidious_trending(instance)
        if items:
            print(f"  Got {len(items)} from {instance}")
            break
    else:
        print("  All Invidious instances failed (502/401/403 or down).")
        items = []

    print(f"[youtube] Total unique: {len(items)}")
    return items

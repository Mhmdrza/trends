"""
YouTube Trending Scraper
Sources: YouTube RSS feeds + Invidious public API (no key needed).
"""

import random
import feedparser
from .base import make_item, safe_get

try:
    from config import INVIDIOUS_INSTANCES, YOUTUBE_CATEGORIES
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import INVIDIOUS_INSTANCES, YOUTUBE_CATEGORIES


def _pick_instance() -> str:
    """Pick a random Invidious instance."""
    return random.choice(INVIDIOUS_INSTANCES)


def scrape_youtube_rss() -> list[dict]:
    """Scrape YouTube trending via RSS feeds."""
    items = []
    # YouTube exposes trending as a playlist-like RSS
    feeds = [
        "https://www.youtube.com/feeds/videos.xml?chart=trending",
    ]
    for feed_url in feeds:
        resp = safe_get(feed_url)
        if not resp:
            continue
        parsed = feedparser.parse(resp.text)
        for entry in parsed.entries[:30]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            views = 0
            # Try to extract view count from media stats
            media = entry.get("media_statistics", {})
            if isinstance(media, dict):
                views = int(media.get("views", 0))

            items.append(make_item(
                source="youtube",
                title=title,
                url=link,
                score=views / 1_000_000 if views else 1.0,
                category="trending",
                extra={"views": views, "author": entry.get("author", "")},
            ))
    return items


def scrape_invidious_trending() -> list[dict]:
    """Scrape trending videos from Invidious API."""
    items = []
    for cat_key, cat_type in YOUTUBE_CATEGORIES.items():
        instance = _pick_instance()
        url = f"{instance}/api/v1/trending"
        params = {}
        if cat_type:
            params["type"] = cat_type

        resp = safe_get(url, params=params)
        if not resp:
            continue

        try:
            data = resp.json()
        except Exception:
            continue

        for video in data[:20]:
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
                category=cat_key,
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
    """Run all YouTube scrapers and return combined items."""
    print("[youtube] Scraping RSS feeds...")
    rss_items = scrape_youtube_rss()
    print(f"  Got {len(rss_items)} from RSS")

    print("[youtube] Scraping Invidious trending...")
    inv_items = scrape_invidious_trending()
    print(f"  Got {len(inv_items)} from Invidious")

    # Deduplicate by video URL
    seen = set()
    combined = []
    for item in rss_items + inv_items:
        url = item["url"]
        if url not in seen:
            seen.add(url)
            combined.append(item)

    print(f"[youtube] Total unique: {len(combined)}")
    return combined

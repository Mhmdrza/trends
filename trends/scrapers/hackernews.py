"""
Hacker News Scraper
Uses the official free Firebase API — no key needed.
"""

from .base import make_item, safe_get

try:
    from config import HN_API_BASE, HN_TOP_LIMIT, HN_NEW_LIMIT
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import HN_API_BASE, HN_TOP_LIMIT, HN_NEW_LIMIT


def _fetch_story(story_id: int):
    """Fetch a single HN story by ID."""
    resp = safe_get(f"{HN_API_BASE}/item/{story_id}.json")
    if not resp:
        return None
    try:
        return resp.json()
    except Exception:
        return None


def _fetch_story_list(endpoint: str, limit: int) -> list[dict]:
    """Fetch a list of story IDs and resolve them."""
    resp = safe_get(f"{HN_API_BASE}/{endpoint}.json")
    if not resp:
        return []

    try:
        story_ids = resp.json()[:limit]
    except Exception:
        return []

    items = []
    for sid in story_ids:
        story = _fetch_story(sid)
        if not story or story.get("type") != "story":
            continue

        title = story.get("title", "")
        url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
        score = story.get("score", 0)
        descendants = story.get("descendants", 0)  # comment count
        by = story.get("by", "")
        time_posted = story.get("time", 0)

        # Score: HN points + comments weighted
        combined_score = (score + descendants * 1.5) / 100.0

        items.append(make_item(
            source="hackernews",
            title=title,
            url=url,
            score=combined_score,
            category="tech",
            extra={
                "hn_id": sid,
                "points": score,
                "comments": descendants,
                "by": by,
                "time": time_posted,
                "hn_url": f"https://news.ycombinator.com/item?id={sid}",
            },
        ))
    return items


def scrape() -> list[dict]:
    """Scrape HN top + new stories."""
    print(f"[hackernews] Fetching top {HN_TOP_LIMIT} stories...")
    top = _fetch_story_list("topstories", HN_TOP_LIMIT)
    print(f"  Got {len(top)} top stories")

    print(f"[hackernews] Fetching new {HN_NEW_LIMIT} stories...")
    new = _fetch_story_list("newstories", HN_NEW_LIMIT)
    print(f"  Got {len(new)} new stories")

    # Deduplicate
    seen = set()
    combined = []
    for item in top + new:
        hn_id = item["extra"].get("hn_id")
        if hn_id not in seen:
            seen.add(hn_id)
            combined.append(item)

    print(f"[hackernews] Total unique: {len(combined)}")
    return combined

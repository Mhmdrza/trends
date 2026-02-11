"""
Reddit Trending Scraper
Uses the free .json endpoints — no API key or OAuth needed.
"""

import time
from .base import make_item, safe_get

try:
    from config import SUBREDDITS, ALL_SUBREDDITS
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import SUBREDDITS, ALL_SUBREDDITS


def _fetch_subreddit(subreddit: str, sort: str = "hot", limit: int = 15) -> list[dict]:
    """Fetch posts from a single subreddit via .json endpoint."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": limit, "raw_json": 1}
    resp = safe_get(url, params=params)
    if not resp:
        return []

    try:
        data = resp.json()
    except Exception:
        return []

    items = []
    children = data.get("data", {}).get("children", [])
    for child in children:
        post = child.get("data", {})
        if not post:
            continue

        title = post.get("title", "")
        permalink = post.get("permalink", "")
        ups = post.get("ups", 0)
        num_comments = post.get("num_comments", 0)
        created_utc = post.get("created_utc", 0)
        subreddit_name = post.get("subreddit", subreddit)
        flair = post.get("link_flair_text", "")

        # Score: combination of upvotes and comments, normalized
        engagement = ups + (num_comments * 2)
        score = engagement / 1000.0

        # Find which category group this subreddit belongs to
        category = "general"
        for cat, subs in SUBREDDITS.items():
            if subreddit_name.lower() in [s.lower() for s in subs]:
                category = cat
                break

        items.append(make_item(
            source="reddit",
            title=title,
            url=f"https://www.reddit.com{permalink}",
            score=score,
            category=category,
            extra={
                "subreddit": subreddit_name,
                "ups": ups,
                "num_comments": num_comments,
                "created_utc": created_utc,
                "flair": flair,
                "engagement": engagement,
            },
        ))
    return items


def scrape() -> list[dict]:
    """Scrape all configured subreddits."""
    all_items = []

    for i, subreddit in enumerate(ALL_SUBREDDITS):
        print(f"[reddit] Scraping r/{subreddit} ({i+1}/{len(ALL_SUBREDDITS)})...")

        # Fetch hot posts
        hot = _fetch_subreddit(subreddit, sort="hot", limit=10)
        all_items.extend(hot)

        # Fetch rising posts (these are the gold — early signals)
        rising = _fetch_subreddit(subreddit, sort="rising", limit=10)
        all_items.extend(rising)

        # Be polite — Reddit rate limits aggressively without auth
        if i < len(ALL_SUBREDDITS) - 1:
            time.sleep(1.5)

    # Deduplicate by URL
    seen = set()
    unique = []
    for item in all_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    print(f"[reddit] Total unique posts: {len(unique)}")
    return unique

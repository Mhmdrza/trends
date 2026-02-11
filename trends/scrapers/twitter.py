"""
Twitter/X Trends Scraper
Uses Nitter instances (RSS + HTML). Many instances are down or 403;
this scraper is best-effort and often returns 0 items.
"""

import random
import feedparser
from bs4 import BeautifulSoup
from .base import make_item, safe_get

try:
    from config import NITTER_INSTANCES, TWITTER_SEARCH_TERMS
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import NITTER_INSTANCES, TWITTER_SEARCH_TERMS


def _pick_instance() -> str:
    return random.choice(NITTER_INSTANCES)


def scrape_nitter_search(term: str) -> list[dict]:
    """Search Nitter for a term and extract tweets."""
    items = []
    instance = _pick_instance()
    url = f"{instance}/search?f=tweets&q={term.replace(' ', '+')}"

    resp = safe_get(url, timeout=10)
    if not resp:
        return items

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        tweets = soup.select(".timeline-item")

        for tweet in tweets[:15]:
            # Extract tweet content
            content_el = tweet.select_one(".tweet-content")
            if not content_el:
                continue
            content = content_el.get_text(strip=True)

            # Extract stats
            stats = tweet.select(".tweet-stat .icon-container")
            comments = 0
            retweets = 0
            likes = 0
            for i, stat in enumerate(stats):
                val_text = stat.get_text(strip=True).replace(",", "")
                try:
                    val = int(val_text) if val_text else 0
                except ValueError:
                    val = 0
                if i == 0:
                    comments = val
                elif i == 1:
                    retweets = val
                elif i == 2:
                    likes = val

            # Extract link
            link_el = tweet.select_one(".tweet-link")
            tweet_path = link_el["href"] if link_el and link_el.has_attr("href") else ""
            tweet_url = f"https://twitter.com{tweet_path}" if tweet_path else ""

            engagement = likes + retweets * 2 + comments * 3
            score = engagement / 1000.0

            # Truncate content for title
            title = content[:120] + ("..." if len(content) > 120 else "")

            items.append(make_item(
                source="twitter",
                title=title,
                url=tweet_url,
                score=score,
                category="social",
                extra={
                    "search_term": term,
                    "likes": likes,
                    "retweets": retweets,
                    "comments": comments,
                    "engagement": engagement,
                    "full_text": content[:500],
                },
            ))
    except Exception as e:
        print(f"  [twitter] Error parsing {instance}: {e}")

    return items


def scrape_nitter_rss(term: str) -> list[dict]:
    """Try Nitter RSS feed for search results."""
    items = []
    instance = _pick_instance()
    url = f"{instance}/search/rss?f=tweets&q={term.replace(' ', '+')}"

    resp = safe_get(url, timeout=10)
    if not resp:
        return items

    try:
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:10]:
            title = entry.get("title", "")[:120]
            link = entry.get("link", "")
            # Convert nitter link to twitter link
            if instance in link:
                link = link.replace(instance, "https://twitter.com")

            items.append(make_item(
                source="twitter",
                title=title,
                url=link,
                score=0.5,  # RSS doesn't give engagement stats
                category="social",
                extra={
                    "search_term": term,
                    "type": "rss",
                },
            ))
    except Exception as e:
        print(f"  [twitter] RSS error: {e}")

    return items


def scrape() -> list[dict]:
    """Scrape Twitter/X via Nitter — best effort."""
    all_items = []

    for term in TWITTER_SEARCH_TERMS:
        print(f"[twitter] Searching '{term}' via Nitter...")

        # Try HTML scraping first, fall back to RSS
        items = scrape_nitter_search(term)
        if not items:
            print(f"  HTML scraping failed, trying RSS...")
            items = scrape_nitter_rss(term)

        all_items.extend(items)
        print(f"  Got {len(items)} tweets for '{term}'")

    # Deduplicate by URL
    seen = set()
    unique = []
    for item in all_items:
        if item["url"] and item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    print(f"[twitter] Total unique tweets: {len(unique)}")
    return unique

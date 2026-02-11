"""
Google Trends Scraper
Uses pytrends (unofficial library) — no API key needed.
"""

from pytrends.request import TrendReq
from .base import make_item

try:
    from config import GOOGLE_TRENDS_GEO, GOOGLE_TRENDS_LANGUAGE
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import GOOGLE_TRENDS_GEO, GOOGLE_TRENDS_LANGUAGE


def _get_pytrends() -> TrendReq:
    """Create a pytrends session."""
    return TrendReq(
        hl=GOOGLE_TRENDS_LANGUAGE,
        tz=360,
        retries=3,
        backoff_factor=1.0,
    )


def scrape_realtime_trending() -> list[dict]:
    """Get real-time trending searches."""
    items = []
    try:
        pt = _get_pytrends()
        # trending_searches returns a DataFrame of currently trending queries
        df = pt.trending_searches(pn="united_states")
        for _, row in df.iterrows():
            query = str(row[0]).strip()
            if query:
                items.append(make_item(
                    source="google_trends",
                    title=query,
                    url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '+')}",
                    score=1.0,  # Trending searches don't have numeric scores
                    category="realtime_trending",
                    extra={"type": "trending_search"},
                ))
    except Exception as e:
        print(f"  [google_trends] Error fetching realtime: {e}")
    return items


def scrape_related_topics() -> list[dict]:
    """
    Get interest over time + related queries for key seed terms.
    This reveals what people are SEARCHING for but may not have content yet.
    """
    items = []
    # Seed terms — broad enough to capture emerging sub-trends
    seed_terms = [
        "AI tools", "side hustle 2026", "creator economy",
        "passive income", "automation",
    ]

    try:
        pt = _get_pytrends()
        for term in seed_terms:
            try:
                pt.build_payload([term], timeframe="now 7-d", geo=GOOGLE_TRENDS_GEO)

                # Related queries — "rising" ones are the gold
                related = pt.related_queries()
                if term in related and related[term].get("rising") is not None:
                    rising_df = related[term]["rising"]
                    if rising_df is not None and not rising_df.empty:
                        for _, row in rising_df.head(10).iterrows():
                            query = str(row.get("query", "")).strip()
                            value = int(row.get("value", 0))
                            if query:
                                items.append(make_item(
                                    source="google_trends",
                                    title=query,
                                    url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '+')}",
                                    score=min(value / 1000.0, 10.0),
                                    velocity=value / 100.0,  # Rising % as velocity
                                    category="rising_query",
                                    extra={
                                        "seed_term": term,
                                        "rise_pct": value,
                                        "type": "related_rising",
                                    },
                                ))
            except Exception as e:
                print(f"  [google_trends] Error for '{term}': {e}")
                continue

    except Exception as e:
        print(f"  [google_trends] Error in related topics: {e}")

    return items


def scrape() -> list[dict]:
    """Run all Google Trends scrapers."""
    print("[google_trends] Fetching realtime trending searches...")
    realtime = scrape_realtime_trending()
    print(f"  Got {len(realtime)} trending searches")

    print("[google_trends] Fetching related rising queries...")
    related = scrape_related_topics()
    print(f"  Got {len(related)} rising queries")

    combined = realtime + related

    # Deduplicate by title (lowercased)
    seen = set()
    unique = []
    for item in combined:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"[google_trends] Total unique: {len(unique)}")
    return unique

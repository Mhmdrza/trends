"""
Google Trends Scraper
Uses pytrends (unofficial library) — no API key needed.
Often rate-limited or blocked in CI; failures are non-fatal.
"""

import time
from .base import make_item

try:
    from config import GOOGLE_TRENDS_GEO, GOOGLE_TRENDS_LANGUAGE
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import GOOGLE_TRENDS_GEO, GOOGLE_TRENDS_LANGUAGE


def _get_pytrends():
    """Create a pytrends session."""
    from pytrends.request import TrendReq
    return TrendReq(
        hl=GOOGLE_TRENDS_LANGUAGE,
        tz=360,
        retries=2,
        backoff_factor=2.0,
    )


def scrape_realtime_trending() -> list:
    """Get real-time trending searches."""
    items = []
    try:
        pt = _get_pytrends()
        df = pt.trending_searches(pn="united_states")
        for _, row in df.iterrows():
            query = str(row[0]).strip()
            if query:
                items.append(make_item(
                    source="google_trends",
                    title=query,
                    url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '+')}",
                    score=1.0,
                    category="realtime_trending",
                    extra={"type": "trending_search"},
                ))
    except Exception as e:
        print(f"  [google_trends] Realtime trending failed: {e}")
    return items


def scrape_related_topics() -> list:
    """Rising related queries for seed terms. One request per term with delay."""
    items = []
    seed_terms = [
        "AI tools", "creator economy", "passive income", "automation",
    ]

    try:
        pt = _get_pytrends()
        for i, term in enumerate(seed_terms):
            if i > 0:
                time.sleep(2)  # Reduce rate-limit risk
            try:
                pt.build_payload([term], timeframe="now 7-d", geo=GOOGLE_TRENDS_GEO or "")
                related = pt.related_queries()
                if term not in related or related[term].get("rising") is None:
                    continue
                rising_df = related[term]["rising"]
                if rising_df is None or rising_df.empty:
                    continue
                for _, row in rising_df.head(10).iterrows():
                    query = str(row.get("query", "")).strip()
                    value = int(row.get("value", 0))
                    if query:
                        items.append(make_item(
                            source="google_trends",
                            title=query,
                            url=f"https://trends.google.com/trends/explore?q={query.replace(' ', '+')}",
                            score=min(value / 1000.0, 10.0),
                            velocity=value / 100.0,
                            category="rising_query",
                            extra={
                                "seed_term": term,
                                "rise_pct": value,
                                "type": "related_rising",
                            },
                        ))
            except Exception as e:
                print(f"  [google_trends] Seed '{term}': {e}")
                continue
    except Exception as e:
        print(f"  [google_trends] Related topics failed: {e}")

    return items


def scrape() -> list:
    """Run Google Trends scrapers. Returns [] if blocked/rate-limited."""
    print("[google_trends] Fetching realtime trending...")
    realtime = scrape_realtime_trending()
    print(f"  Realtime: {len(realtime)}")

    print("[google_trends] Fetching related rising queries...")
    related = scrape_related_topics()
    print(f"  Rising: {len(related)}")

    combined = realtime + related
    seen = set()
    unique = []
    for item in combined:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    print(f"[google_trends] Total unique: {len(unique)}")
    return unique

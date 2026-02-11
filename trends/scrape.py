"""
Main scraper orchestrator — runs all scrapers and saves raw data.
"""

import json
import os
from datetime import datetime, timezone

from scrapers.youtube import scrape as scrape_youtube
from scrapers.reddit import scrape as scrape_reddit
from scrapers.google_trends import scrape as scrape_google_trends
from scrapers.hackernews import scrape as scrape_hackernews
from scrapers.twitter import scrape as scrape_twitter
from config import DATA_DIR


def run_all_scrapers() -> dict:
    """Run every scraper and return combined results."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": {},
        "all_items": [],
    }

    scrapers = [
        ("youtube", scrape_youtube),
        ("reddit", scrape_reddit),
        ("google_trends", scrape_google_trends),
        ("hackernews", scrape_hackernews),
        ("twitter", scrape_twitter),
    ]

    for name, scrape_fn in scrapers:
        print(f"\n{'='*60}")
        print(f"  Running: {name}")
        print(f"{'='*60}")
        try:
            items = scrape_fn()
            results["sources"][name] = {
                "count": len(items),
                "status": "ok",
            }
            results["all_items"].extend(items)
        except Exception as e:
            print(f"  [FAILED] {name}: {e}")
            results["sources"][name] = {
                "count": 0,
                "status": f"error: {str(e)[:200]}",
            }

    return results


def save_results(results: dict):
    """Save scrape results to data/ directory."""
    # Save latest snapshot
    latest_path = os.path.join(DATA_DIR, "latest_scrape.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved latest scrape: {latest_path} ({len(results['all_items'])} items)")

    # Also save timestamped archive (for historical tracking)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    archive_path = os.path.join(DATA_DIR, f"scrape_{ts}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved archive: {archive_path}")

    # Prune old archives — keep last 30 days (max ~120 files at 4x/day)
    _prune_archives(max_files=120)


def _prune_archives(max_files: int = 120):
    """Remove oldest archive files if we exceed max."""
    archives = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith("scrape_") and f.endswith(".json")
    ])
    if len(archives) > max_files:
        for old_file in archives[:len(archives) - max_files]:
            os.remove(os.path.join(DATA_DIR, old_file))
            print(f"  Pruned old archive: {old_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("  TREND MONITOR — Scraping all sources")
    print("=" * 60)

    results = run_all_scrapers()
    save_results(results)

    print("\n" + "=" * 60)
    print("  SCRAPE COMPLETE")
    for src, info in results["sources"].items():
        status = "OK" if info["status"] == "ok" else "FAIL"
        print(f"    {src:20s} — {info['count']:4d} items [{status}]")
    print(f"  Total items: {len(results['all_items'])}")
    print("=" * 60)

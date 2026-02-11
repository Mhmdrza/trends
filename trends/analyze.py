"""
Trend Analyzer — The Intelligence Layer

Cross-platform gap detection, velocity scoring, niche opportunity
finding, bridge topic detection, and linguistic void discovery.
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import log2

from config import DATA_DIR, WEIGHTS, INTEREST_TAGS, SUBREDDITS


def load_latest_scrape() -> dict:
    """Load the most recent scrape data."""
    path = os.path.join(DATA_DIR, "latest_scrape.json")
    if not os.path.exists(path):
        print("[analyze] No scrape data found!")
        return {"all_items": [], "timestamp": "", "sources": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_historical_scrapes(max_files: int = 20) -> list[dict]:
    """Load recent historical scrapes for velocity calculation."""
    archives = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith("scrape_") and f.endswith(".json")
    ], reverse=True)[:max_files]

    history = []
    for fname in archives:
        path = os.path.join(DATA_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                history.append(json.load(f))
        except Exception:
            continue
    return history


# ── Text Normalization ────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or",
        "if", "while", "about", "up", "it", "its", "my", "your", "his",
        "her", "their", "our", "this", "that", "these", "those", "what",
        "which", "who", "whom", "i", "you", "he", "she", "we", "they",
        "me", "him", "us", "them", "new", "get", "got", "like", "one",
    }
    words = _normalize(text).split()
    return {w for w in words if len(w) > 2 and w not in stop_words}


# ── 1. Cross-Platform Gap Detector ───────────────────────────────────────────

def detect_cross_platform_gaps(items: list[dict]) -> list[dict]:
    """
    Find topics that are trending on some platforms but MISSING from others.
    A topic hot on Reddit/HN but absent from YouTube = content opportunity.
    """
    # Group items by source
    by_source = defaultdict(list)
    for item in items:
        by_source[item["source"]].append(item)

    # Build keyword frequency per platform
    platform_keywords = {}
    for source, source_items in by_source.items():
        kw_counter = Counter()
        for item in source_items:
            keywords = _extract_keywords(item["title"])
            kw_counter.update(keywords)
        platform_keywords[source] = kw_counter

    # Find keywords that appear on 2+ platforms but NOT on youtube
    all_platforms = set(platform_keywords.keys())
    text_platforms = all_platforms - {"youtube"}  # Discussion platforms
    youtube_keywords = set(platform_keywords.get("youtube", {}).keys())

    gaps = []
    # Check every keyword from text platforms
    keyword_presence = defaultdict(lambda: {"platforms": set(), "total_count": 0})
    for source in text_platforms:
        for kw, count in platform_keywords[source].items():
            keyword_presence[kw]["platforms"].add(source)
            keyword_presence[kw]["total_count"] += count

    for kw, info in keyword_presence.items():
        platforms = info["platforms"]
        count = info["total_count"]

        # Must be on 2+ text platforms and NOT on YouTube
        if len(platforms) >= 2 and kw not in youtube_keywords and count >= 3:
            # Find representative items
            examples = []
            for item in items:
                if kw in _extract_keywords(item["title"]):
                    examples.append({
                        "title": item["title"],
                        "source": item["source"],
                        "url": item["url"],
                        "score": item["score"],
                    })

            gaps.append({
                "keyword": kw,
                "present_on": sorted(platforms),
                "missing_from": ["youtube"],
                "mention_count": count,
                "opportunity_score": round(
                    count * len(platforms) * WEIGHTS["cross_platform_presence"], 2
                ),
                "examples": examples[:5],
            })

    # Sort by opportunity score
    gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return gaps[:50]


# ── 2. Velocity Scoring ──────────────────────────────────────────────────────

def calculate_velocity(items: list[dict], history: list[dict]) -> list[dict]:
    """
    Calculate how fast topics are accelerating.
    Not just "what's popular" but "what's growing fastest".
    """
    if not history:
        # No history — use raw scores as proxy
        velocity_items = []
        for item in items:
            velocity_items.append({
                **item,
                "velocity": item.get("score", 0) * 1.5,
                "velocity_label": "new",
            })
        velocity_items.sort(key=lambda x: x["velocity"], reverse=True)
        return velocity_items[:50]

    # Build keyword frequency from current vs historical
    current_keywords = Counter()
    for item in items:
        current_keywords.update(_extract_keywords(item["title"]))

    historical_keywords = Counter()
    for scrape in history[1:]:  # Skip first (it's close to current)
        for item in scrape.get("all_items", []):
            historical_keywords.update(_extract_keywords(item["title"]))

    # Normalize by number of scrapes
    num_historical = max(len(history) - 1, 1)
    historical_avg = {
        k: v / num_historical for k, v in historical_keywords.items()
    }

    # Calculate velocity = (current_freq - historical_avg) / historical_avg
    keyword_velocity = {}
    for kw, current_count in current_keywords.items():
        hist_avg = historical_avg.get(kw, 0)
        if hist_avg > 0:
            velocity = (current_count - hist_avg) / hist_avg
        else:
            velocity = current_count * 2.0  # Brand new = high velocity
        keyword_velocity[kw] = velocity

    # Score each item by the velocity of its keywords
    velocity_items = []
    for item in items:
        kws = _extract_keywords(item["title"])
        if not kws:
            continue
        avg_velocity = sum(keyword_velocity.get(k, 0) for k in kws) / len(kws)

        label = "declining"
        if avg_velocity > 2.0:
            label = "exploding"
        elif avg_velocity > 0.5:
            label = "rising"
        elif avg_velocity > -0.2:
            label = "stable"

        velocity_items.append({
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "category": item["category"],
            "base_score": item["score"],
            "velocity": round(avg_velocity, 3),
            "velocity_label": label,
            "combined_score": round(
                item["score"] * WEIGHTS["velocity"] * max(avg_velocity, 0.1), 2
            ),
        })

    velocity_items.sort(key=lambda x: x["velocity"], reverse=True)
    return velocity_items[:50]


# ── 3. Niche Opportunity Finder ──────────────────────────────────────────────

def find_niche_opportunities(items: list[dict]) -> list[dict]:
    """
    Topics with high interest signals but low content competition.
    High Google Trends interest + low YouTube presence = gold.
    """
    # Collect search-interest signals (Google Trends)
    search_signals = {}
    for item in items:
        if item["source"] == "google_trends":
            kws = _extract_keywords(item["title"])
            for kw in kws:
                if kw not in search_signals:
                    search_signals[kw] = {
                        "demand_score": 0,
                        "examples": [],
                    }
                search_signals[kw]["demand_score"] += item["score"]
                search_signals[kw]["examples"].append(item["title"])

    # Collect YouTube supply signals
    youtube_keywords = Counter()
    for item in items:
        if item["source"] == "youtube":
            youtube_keywords.update(_extract_keywords(item["title"]))

    # Calculate niche score = demand / (supply + 1)
    niches = []
    for kw, info in search_signals.items():
        supply = youtube_keywords.get(kw, 0)
        demand = info["demand_score"]
        niche_score = demand / (supply + 1) * WEIGHTS["low_competition"]

        # Boost if matches personal interest tags
        interest_boost = 1.0
        for tag in INTEREST_TAGS:
            if kw in _normalize(tag):
                interest_boost = 1.5
                break

        niches.append({
            "keyword": kw,
            "demand_score": round(demand, 2),
            "youtube_supply": supply,
            "niche_score": round(niche_score * interest_boost, 2),
            "interest_match": interest_boost > 1.0,
            "related_queries": list(set(info["examples"]))[:5],
        })

    niches.sort(key=lambda x: x["niche_score"], reverse=True)
    return niches[:40]


# ── 4. Bridge Topic Detector ─────────────────────────────────────────────────

def detect_bridge_topics(items: list[dict]) -> list[dict]:
    """
    Find topics that span normally disconnected communities.
    E.g., a topic trending in both r/fitness AND r/programming = crossover niche.
    """
    # Map items to their community group
    item_communities = []
    for item in items:
        communities = set()
        if item["source"] == "reddit":
            sub = item.get("extra", {}).get("subreddit", "").lower()
            for group_name, subs in SUBREDDITS.items():
                if sub in [s.lower() for s in subs]:
                    communities.add(group_name)
        elif item["source"] == "hackernews":
            communities.add("tech")
        elif item["source"] == "google_trends":
            communities.add("mainstream")
        elif item["source"] == "youtube":
            communities.add("content")
        elif item["source"] == "twitter":
            communities.add("social")

        if communities:
            item_communities.append((item, communities))

    # Group by keywords and collect which communities discuss each keyword
    keyword_communities = defaultdict(lambda: {
        "communities": set(),
        "items": [],
        "total_score": 0,
    })

    for item, communities in item_communities:
        for kw in _extract_keywords(item["title"]):
            keyword_communities[kw]["communities"].update(communities)
            keyword_communities[kw]["items"].append(item)
            keyword_communities[kw]["total_score"] += item["score"]

    # Find bridge keywords — appearing in 2+ DIFFERENT community groups
    bridges = []
    for kw, info in keyword_communities.items():
        if len(info["communities"]) >= 2:
            bridge_strength = (
                len(info["communities"])
                * info["total_score"]
                * WEIGHTS["community_bridge"]
            )
            bridges.append({
                "keyword": kw,
                "communities": sorted(info["communities"]),
                "num_communities": len(info["communities"]),
                "bridge_score": round(bridge_strength, 2),
                "total_mentions": len(info["items"]),
                "examples": [
                    {
                        "title": it["title"],
                        "source": it["source"],
                        "category": it["category"],
                    }
                    for it in info["items"][:5]
                ],
            })

    bridges.sort(key=lambda x: x["bridge_score"], reverse=True)
    return bridges[:40]


# ── 5. Linguistic Void Detection ─────────────────────────────────────────────

def detect_linguistic_voids(items: list[dict]) -> list[dict]:
    """
    Find clusters of discussion around concepts that don't have a clear name yet.
    These are "feelings people have but don't have a word for" — naming them = power.

    Strategy: Find keyword clusters that co-occur frequently but lack a single
    dominant term. The cluster IS the unnamed concept.
    """
    # Build co-occurrence matrix
    co_occur = defaultdict(Counter)
    for item in items:
        kws = sorted(_extract_keywords(item["title"]))
        for i, kw1 in enumerate(kws):
            for kw2 in kws[i + 1:]:
                co_occur[kw1][kw2] += 1
                co_occur[kw2][kw1] += 1

    # Find tight clusters — groups of 3+ keywords that all co-occur
    keyword_freq = Counter()
    for item in items:
        keyword_freq.update(_extract_keywords(item["title"]))

    # Start with high co-occurring pairs
    strong_pairs = []
    for kw1, partners in co_occur.items():
        for kw2, count in partners.items():
            if count >= 3 and kw1 < kw2:  # Avoid duplicates
                strong_pairs.append((kw1, kw2, count))

    strong_pairs.sort(key=lambda x: x[2], reverse=True)

    # Expand pairs into clusters
    voids = []
    used = set()

    for kw1, kw2, pair_count in strong_pairs[:100]:
        if kw1 in used or kw2 in used:
            continue

        # Find other keywords that co-occur with BOTH kw1 and kw2
        cluster = {kw1, kw2}
        for candidate in co_occur[kw1]:
            if candidate in co_occur[kw2] and candidate not in used:
                if co_occur[kw1][candidate] >= 2 and co_occur[kw2][candidate] >= 2:
                    cluster.add(candidate)

        if len(cluster) >= 3:
            # This cluster of keywords describes something people discuss
            # but may not have a single name for
            cluster_list = sorted(cluster)
            concept_hint = " + ".join(cluster_list[:4])

            # Find example items that contain 2+ cluster keywords
            examples = []
            for item in items:
                item_kws = _extract_keywords(item["title"])
                overlap = item_kws & cluster
                if len(overlap) >= 2:
                    examples.append({
                        "title": item["title"],
                        "source": item["source"],
                        "matching_keywords": sorted(overlap),
                    })

            if examples:
                voids.append({
                    "concept_cluster": cluster_list,
                    "concept_hint": concept_hint,
                    "cluster_size": len(cluster),
                    "discussion_count": len(examples),
                    "void_score": round(
                        len(cluster) * len(examples) * pair_count * 0.5, 2
                    ),
                    "examples": examples[:5],
                })
                used.update(cluster)

    voids.sort(key=lambda x: x["void_score"], reverse=True)
    return voids[:20]


# ── 6. Interest-Relevance Scoring ────────────────────────────────────────────

def score_personal_relevance(items: list[dict]) -> list[dict]:
    """Score items by relevance to personal interest tags."""
    interest_kws = set()
    for tag in INTEREST_TAGS:
        interest_kws.update(_extract_keywords(tag))

    scored = []
    for item in items:
        item_kws = _extract_keywords(item["title"])
        overlap = item_kws & interest_kws
        relevance = len(overlap) / max(len(interest_kws), 1)
        if relevance > 0:
            scored.append({
                "title": item["title"],
                "url": item["url"],
                "source": item["source"],
                "category": item["category"],
                "score": item["score"],
                "relevance": round(relevance, 3),
                "matching_tags": sorted(overlap),
            })

    scored.sort(key=lambda x: (x["relevance"], x["score"]), reverse=True)
    return scored[:30]


# ── Main Analysis Pipeline ────────────────────────────────────────────────────

def run_analysis():
    """Run all analyzers and save results."""
    print("=" * 60)
    print("  TREND ANALYZER — Cross-platform intelligence")
    print("=" * 60)

    data = load_latest_scrape()
    items = data.get("all_items", [])
    if not items:
        print("[analyze] No items to analyze!")
        return

    history = load_historical_scrapes()
    print(f"\nLoaded {len(items)} items, {len(history)} historical scrapes\n")

    # Run all analyzers
    print("[1/6] Cross-platform gap detection...")
    gaps = detect_cross_platform_gaps(items)
    print(f"  Found {len(gaps)} gap opportunities")

    print("[2/6] Velocity scoring...")
    velocity = calculate_velocity(items, history)
    print(f"  Scored {len(velocity)} items by velocity")

    print("[3/6] Niche opportunity finding...")
    niches = find_niche_opportunities(items)
    print(f"  Found {len(niches)} niche opportunities")

    print("[4/6] Bridge topic detection...")
    bridges = detect_bridge_topics(items)
    print(f"  Found {len(bridges)} bridge topics")

    print("[5/6] Linguistic void detection...")
    voids = detect_linguistic_voids(items)
    print(f"  Found {len(voids)} unnamed concept clusters")

    print("[6/6] Personal relevance scoring...")
    relevant = score_personal_relevance(items)
    print(f"  Found {len(relevant)} personally relevant items")

    # Compile analysis results
    analysis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scrape_timestamp": data.get("timestamp", ""),
        "total_items_analyzed": len(items),
        "sources_summary": data.get("sources", {}),
        "cross_platform_gaps": gaps,
        "velocity_leaders": velocity,
        "niche_opportunities": niches,
        "bridge_topics": bridges,
        "linguistic_voids": voids,
        "personal_relevance": relevant,
    }

    # Save
    output_path = os.path.join(DATA_DIR, "analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"\nAnalysis saved: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("  ANALYSIS SUMMARY")
    print("=" * 60)
    if gaps:
        print(f"\n  Top 5 Content Gaps (trending elsewhere, missing on YouTube):")
        for g in gaps[:5]:
            print(f"    - '{g['keyword']}' ({g['mention_count']} mentions on {g['present_on']})")
    if velocity:
        print(f"\n  Top 5 Fastest Rising:")
        for v in velocity[:5]:
            print(f"    - [{v['velocity_label']}] {v['title'][:60]}... (v={v['velocity']:.1f})")
    if niches:
        print(f"\n  Top 5 Niche Opportunities (high demand, low YT supply):")
        for n in niches[:5]:
            print(f"    - '{n['keyword']}' (demand={n['demand_score']}, YT supply={n['youtube_supply']})")
    if bridges:
        print(f"\n  Top 5 Bridge Topics (cross-community):")
        for b in bridges[:5]:
            print(f"    - '{b['keyword']}' bridges {b['communities']}")
    if voids:
        print(f"\n  Top 3 Linguistic Voids (unnamed concepts):")
        for v in voids[:3]:
            print(f"    - Cluster: {v['concept_hint']} ({v['discussion_count']} discussions)")
    print("=" * 60)


if __name__ == "__main__":
    run_analysis()

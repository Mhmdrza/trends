"""
Dashboard Builder — Generates a static HTML dashboard from analysis data.
Beautiful dark-mode UI, responsive, zero dependencies at runtime.
"""

import json
import os
import html

from config import DATA_DIR, DOCS_DIR


def load_analysis() -> dict:
    """Load analysis results."""
    path = os.path.join(DATA_DIR, "analysis.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(text: str) -> str:
    """HTML escape."""
    return html.escape(str(text))


def build_html(analysis: dict) -> str:
    """Build the complete dashboard HTML."""
    timestamp = analysis.get("timestamp", "N/A")
    total = analysis.get("total_items_analyzed", 0)
    sources = analysis.get("sources_summary", {})
    gaps = analysis.get("cross_platform_gaps", [])
    velocity = analysis.get("velocity_leaders", [])
    niches = analysis.get("niche_opportunities", [])
    bridges = analysis.get("bridge_topics", [])
    voids = analysis.get("linguistic_voids", [])
    relevant = analysis.get("personal_relevance", [])

    # Source stats bar
    source_chips = ""
    for src, info in sources.items():
        status_class = "ok" if info.get("status") == "ok" else "err"
        source_chips += (
            f'<span class="chip {status_class}">'
            f'{esc(src)}: {info.get("count", 0)}'
            f'</span>\n'
        )

    # Gap rows
    gap_rows = ""
    for g in gaps[:25]:
        platforms = ", ".join(g["present_on"])
        examples_html = ""
        for ex in g.get("examples", [])[:3]:
            examples_html += (
                f'<a href="{esc(ex["url"])}" target="_blank" class="ex-link">'
                f'{esc(ex["title"][:80])}</a> '
            )
        gap_rows += f"""<tr>
            <td class="kw">{esc(g['keyword'])}</td>
            <td>{platforms}</td>
            <td class="num">{g['mention_count']}</td>
            <td class="num score">{g['opportunity_score']}</td>
            <td class="examples">{examples_html}</td>
        </tr>\n"""

    # Velocity rows
    velocity_rows = ""
    for v in velocity[:25]:
        label = v.get("velocity_label", "?")
        label_class = {
            "exploding": "vel-exploding",
            "rising": "vel-rising",
            "stable": "vel-stable",
            "declining": "vel-declining",
            "new": "vel-new",
        }.get(label, "")
        velocity_rows += f"""<tr>
            <td><span class="vel-badge {label_class}">{esc(label)}</span></td>
            <td><a href="{esc(v.get('url', '#'))}" target="_blank">{esc(v['title'][:90])}</a></td>
            <td class="chip-src">{esc(v.get('source', ''))}</td>
            <td class="num">{v.get('velocity', 0):.2f}</td>
            <td class="num">{v.get('combined_score', v.get('score', 0)):.2f}</td>
        </tr>\n"""

    # Niche rows
    niche_rows = ""
    for n in niches[:25]:
        interest_mark = " *" if n.get("interest_match") else ""
        queries = ", ".join(n.get("related_queries", [])[:3])
        niche_rows += f"""<tr>
            <td class="kw">{esc(n['keyword'])}{interest_mark}</td>
            <td class="num">{n['demand_score']}</td>
            <td class="num">{n['youtube_supply']}</td>
            <td class="num score">{n['niche_score']}</td>
            <td class="examples">{esc(queries)}</td>
        </tr>\n"""

    # Bridge rows
    bridge_rows = ""
    for b in bridges[:25]:
        communities = ", ".join(b["communities"])
        examples_html = ""
        for ex in b.get("examples", [])[:2]:
            examples_html += f'<span class="chip">{esc(ex["source"])}: {esc(ex["title"][:50])}</span> '
        bridge_rows += f"""<tr>
            <td class="kw">{esc(b['keyword'])}</td>
            <td>{esc(communities)}</td>
            <td class="num">{b['num_communities']}</td>
            <td class="num">{b['total_mentions']}</td>
            <td class="num score">{b['bridge_score']}</td>
        </tr>\n"""

    # Void rows
    void_rows = ""
    for v in voids[:15]:
        cluster = ", ".join(v["concept_cluster"][:5])
        examples_html = ""
        for ex in v.get("examples", [])[:2]:
            examples_html += f'<div class="void-ex">{esc(ex["source"])}: {esc(ex["title"][:70])}</div>'
        void_rows += f"""<tr>
            <td class="kw">{esc(v['concept_hint'])}</td>
            <td>{esc(cluster)}</td>
            <td class="num">{v['cluster_size']}</td>
            <td class="num">{v['discussion_count']}</td>
            <td class="num score">{v['void_score']}</td>
        </tr>\n"""

    # Relevant rows
    relevant_rows = ""
    for r in relevant[:20]:
        tags = ", ".join(r.get("matching_tags", []))
        relevant_rows += f"""<tr>
            <td><a href="{esc(r.get('url', '#'))}" target="_blank">{esc(r['title'][:90])}</a></td>
            <td class="chip-src">{esc(r.get('source', ''))}</td>
            <td class="num">{r.get('relevance', 0):.2f}</td>
            <td>{esc(tags)}</td>
        </tr>\n"""

    # JSON data for potential JS interactivity
    analysis_json = json.dumps(analysis, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trend Monitor — Intelligence Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

:root {{
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --surface3: #22222e;
    --border: #2a2a3a;
    --text: #e0e0ec;
    --text2: #8888a0;
    --text3: #555568;
    --accent: #6c5ce7;
    --accent2: #a29bfe;
    --green: #00b894;
    --green-soft: rgba(0,184,148,0.12);
    --red: #ff6b6b;
    --red-soft: rgba(255,107,107,0.12);
    --orange: #fdcb6e;
    --orange-soft: rgba(253,203,110,0.12);
    --blue: #74b9ff;
    --blue-soft: rgba(116,185,255,0.12);
    --purple: #a29bfe;
    --purple-soft: rgba(162,155,254,0.12);
    --cyan: #81ecec;
    --radius: 8px;
    --radius-lg: 12px;
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
    --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}}

body {{
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    min-height: 100vh;
}}

/* ── Header ── */
.header {{
    background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
    border-bottom: 1px solid var(--border);
    padding: 24px 32px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
}}
.header h1 {{
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, var(--accent2), var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.header .meta {{
    color: var(--text2);
    font-size: 0.85rem;
    margin-top: 6px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
}}

/* ── Chips ── */
.chip {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    background: var(--surface3);
    color: var(--text2);
    border: 1px solid var(--border);
}}
.chip.ok {{ background: var(--green-soft); color: var(--green); border-color: var(--green); }}
.chip.err {{ background: var(--red-soft); color: var(--red); border-color: var(--red); }}
.chip-src {{
    font-size: 0.75rem;
    color: var(--text3);
    font-family: var(--mono);
}}

/* ── Main ── */
.main {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
}}

/* ── Section ── */
.section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    margin-bottom: 24px;
    overflow: hidden;
}}
.section-header {{
    padding: 18px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
}}
.section-header h2 {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
}}
.section-header .badge {{
    background: var(--accent);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}}
.section-header .desc {{
    color: var(--text3);
    font-size: 0.8rem;
    margin-left: auto;
}}

/* ── Table ── */
.tbl-wrap {{
    overflow-x: auto;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
thead th {{
    text-align: left;
    padding: 10px 16px;
    background: var(--surface2);
    color: var(--text2);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
}}
tbody tr {{
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
}}
tbody tr:hover {{
    background: var(--surface2);
}}
td {{
    padding: 10px 16px;
    vertical-align: top;
}}
td.kw {{
    font-weight: 600;
    color: var(--accent2);
    font-family: var(--mono);
    font-size: 0.82rem;
    white-space: nowrap;
}}
td.num {{
    font-family: var(--mono);
    text-align: right;
    white-space: nowrap;
}}
td.score {{
    color: var(--green);
    font-weight: 600;
}}
td.examples {{
    font-size: 0.78rem;
    color: var(--text2);
    max-width: 320px;
}}
a {{
    color: var(--blue);
    text-decoration: none;
}}
a:hover {{
    text-decoration: underline;
}}
.ex-link {{
    display: inline-block;
    margin: 2px 0;
    color: var(--text2);
    font-size: 0.76rem;
}}
.ex-link:hover {{ color: var(--blue); }}

/* ── Velocity badges ── */
.vel-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.vel-exploding {{ background: var(--red-soft); color: var(--red); }}
.vel-rising {{ background: var(--orange-soft); color: var(--orange); }}
.vel-stable {{ background: var(--blue-soft); color: var(--blue); }}
.vel-declining {{ background: var(--surface3); color: var(--text3); }}
.vel-new {{ background: var(--purple-soft); color: var(--purple); }}

/* ── Void examples ── */
.void-ex {{
    font-size: 0.76rem;
    color: var(--text3);
    padding: 2px 0;
}}

/* ── Stats grid ── */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    padding: 20px 24px;
}}
.stat-card {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    text-align: center;
}}
.stat-card .num {{
    font-size: 2rem;
    font-weight: 700;
    font-family: var(--mono);
    background: linear-gradient(135deg, var(--accent2), var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.stat-card .label {{
    color: var(--text3);
    font-size: 0.78rem;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── Nav tabs ── */
.nav {{
    display: flex;
    gap: 4px;
    padding: 16px 24px 0;
    flex-wrap: wrap;
}}
.nav-btn {{
    padding: 8px 18px;
    border-radius: var(--radius) var(--radius) 0 0;
    background: var(--surface2);
    color: var(--text2);
    border: 1px solid var(--border);
    border-bottom: none;
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 500;
    font-family: var(--font);
    transition: all 0.15s;
}}
.nav-btn:hover {{ color: var(--text); background: var(--surface3); }}
.nav-btn.active {{
    background: var(--surface);
    color: var(--accent2);
    border-color: var(--accent);
    border-bottom: 2px solid var(--surface);
    margin-bottom: -1px;
    position: relative;
    z-index: 1;
}}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

/* ── Responsive ── */
@media (max-width: 768px) {{
    .header {{ padding: 16px; }}
    .main {{ padding: 12px; }}
    .section-header {{ flex-wrap: wrap; }}
    .section-header .desc {{ margin-left: 0; margin-top: 8px; }}
    td {{ padding: 8px 10px; font-size: 0.78rem; }}
    .nav {{ gap: 2px; }}
    .nav-btn {{ padding: 6px 12px; font-size: 0.75rem; }}
}}

/* ── Empty state ── */
.empty {{
    padding: 40px;
    text-align: center;
    color: var(--text3);
}}
</style>
</head>
<body>

<div class="header">
    <h1>Trend Monitor</h1>
    <div class="meta">
        <span>Updated: {esc(timestamp[:19].replace('T', ' '))} UTC</span>
        <span>{total} items analyzed</span>
        {source_chips}
    </div>
</div>

<div class="main">

<!-- Stats Overview -->
<div class="section">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="num">{len(gaps)}</div>
            <div class="label">Content Gaps</div>
        </div>
        <div class="stat-card">
            <div class="num">{len([v for v in velocity if v.get('velocity_label') in ('exploding','rising')])}</div>
            <div class="label">Rising Trends</div>
        </div>
        <div class="stat-card">
            <div class="num">{len(niches)}</div>
            <div class="label">Niche Opportunities</div>
        </div>
        <div class="stat-card">
            <div class="num">{len(bridges)}</div>
            <div class="label">Bridge Topics</div>
        </div>
        <div class="stat-card">
            <div class="num">{len(voids)}</div>
            <div class="label">Linguistic Voids</div>
        </div>
        <div class="stat-card">
            <div class="num">{total}</div>
            <div class="label">Total Signals</div>
        </div>
    </div>
</div>

<!-- Navigation Tabs -->
<div class="nav">
    <button class="nav-btn active" data-tab="gaps">Content Gaps</button>
    <button class="nav-btn" data-tab="velocity">Velocity</button>
    <button class="nav-btn" data-tab="niches">Niche Finder</button>
    <button class="nav-btn" data-tab="bridges">Bridge Topics</button>
    <button class="nav-btn" data-tab="voids">Linguistic Voids</button>
    <button class="nav-btn" data-tab="relevant">For You</button>
</div>

<!-- Tab 1: Content Gaps -->
<div class="section tab-panel active" id="tab-gaps">
    <div class="section-header">
        <h2>Cross-Platform Content Gaps</h2>
        <span class="badge">{len(gaps)}</span>
        <span class="desc">Trending on discussion platforms but MISSING from YouTube</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Keyword</th><th>Present On</th><th>Mentions</th><th>Score</th><th>Examples</th></tr></thead><tbody>" + gap_rows + "</tbody></table>" if gaps else '<div class="empty">No gaps detected yet. Run more scrapes to build data.</div>'}
    </div>
</div>

<!-- Tab 2: Velocity -->
<div class="section tab-panel" id="tab-velocity">
    <div class="section-header">
        <h2>Velocity Leaders</h2>
        <span class="badge">{len(velocity)}</span>
        <span class="desc">Topics accelerating fastest right now</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Status</th><th>Title</th><th>Source</th><th>Velocity</th><th>Score</th></tr></thead><tbody>" + velocity_rows + "</tbody></table>" if velocity else '<div class="empty">No velocity data yet.</div>'}
    </div>
</div>

<!-- Tab 3: Niche Finder -->
<div class="section tab-panel" id="tab-niches">
    <div class="section-header">
        <h2>Niche Opportunities</h2>
        <span class="badge">{len(niches)}</span>
        <span class="desc">High search demand + low YouTube supply = gold (* = matches your interests)</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Keyword</th><th>Demand</th><th>YT Supply</th><th>Niche Score</th><th>Related</th></tr></thead><tbody>" + niche_rows + "</tbody></table>" if niches else '<div class="empty">No niche data yet. Google Trends scrape needed.</div>'}
    </div>
</div>

<!-- Tab 4: Bridge Topics -->
<div class="section tab-panel" id="tab-bridges">
    <div class="section-header">
        <h2>Bridge Topics</h2>
        <span class="badge">{len(bridges)}</span>
        <span class="desc">Topics connecting disconnected communities — structural holes</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Keyword</th><th>Communities</th><th>Bridges</th><th>Mentions</th><th>Score</th></tr></thead><tbody>" + bridge_rows + "</tbody></table>" if bridges else '<div class="empty">No bridge topics found yet.</div>'}
    </div>
</div>

<!-- Tab 5: Linguistic Voids -->
<div class="section tab-panel" id="tab-voids">
    <div class="section-header">
        <h2>Linguistic Voids</h2>
        <span class="badge">{len(voids)}</span>
        <span class="desc">Unnamed concepts people discuss but have no word for yet — name them, own them</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Concept Hint</th><th>Keyword Cluster</th><th>Size</th><th>Discussions</th><th>Score</th></tr></thead><tbody>" + void_rows + "</tbody></table>" if voids else '<div class="empty">Not enough data for void detection. Need more scrape history.</div>'}
    </div>
</div>

<!-- Tab 6: Personal Relevance -->
<div class="section tab-panel" id="tab-relevant">
    <div class="section-header">
        <h2>For You</h2>
        <span class="badge">{len(relevant)}</span>
        <span class="desc">Matching your interest tags</span>
    </div>
    <div class="tbl-wrap">
    {"<table><thead><tr><th>Title</th><th>Source</th><th>Relevance</th><th>Matching Tags</th></tr></thead><tbody>" + relevant_rows + "</tbody></table>" if relevant else '<div class="empty">No matching items. Update INTEREST_TAGS in config.</div>'}
    </div>
</div>

</div><!-- /.main -->

<script>
// Tab switching
document.querySelectorAll('.nav-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    }});
}});

// Store raw data for potential future JS interactivity
window.__TREND_DATA__ = {analysis_json};
</script>
</body>
</html>"""


def build():
    """Load analysis and generate dashboard."""
    print("[dashboard] Loading analysis data...")
    analysis = load_analysis()
    if not analysis:
        print("[dashboard] No analysis data found. Generating empty dashboard.")
        analysis = {
            "timestamp": "N/A",
            "total_items_analyzed": 0,
            "sources_summary": {},
            "cross_platform_gaps": [],
            "velocity_leaders": [],
            "niche_opportunities": [],
            "bridge_topics": [],
            "linguistic_voids": [],
            "personal_relevance": [],
        }

    print("[dashboard] Building HTML...")
    html_content = build_html(analysis)

    output_path = os.path.join(DOCS_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = len(html_content.encode()) / 1024
    print(f"[dashboard] Generated: {output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Self-hosted matrix-style GitHub stats cards generator.
Fetches live data from the GitHub API and renders two SVG cards:
  assets/github-stats.svg  — stars, repos, commits, followers, account age
  assets/top-langs.svg     — language breakdown by bytes

Uses ONLY the Python stdlib so it runs anywhere (GitHub Actions, CI, local).
Token (optional, raises rate limits): env GH_STATS_TOKEN or GITHUB_TOKEN.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

OWNER = "SSSchangerSSS"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
OUT_DIR = os.path.abspath(OUT_DIR)

BG = "#0d1117"
BORDER = "#00FF41"
HEADER = "#00FF41"
LABEL = "#8b949e"
VALUE = "#00FF41"
DIM = "#003b00"
FONT = "Consolas, 'DejaVu Sans Mono', 'Courier New', monospace"

# matrix-compatible language palette (greens -> teals -> lime)
LANG_COLORS = ["#00FF41", "#00C853", "#64DD17", "#00BFA5", "#AEEA00", "#26A69A", "#9CCC65", "#C6FF00"]


def api_get(path, token):
    url = path if path.startswith("http") else "https://api.github.com" + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stats-card-generator")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_stats(token):
    stats = {"stars": 0, "public_repos": 0, "followers": 0, "commits": None,
             "created_at": None, "langs": {}}
    try:
        u = api_get(f"/users/{OWNER}", token)
        stats["public_repos"] = u.get("public_repos", 0)
        stats["followers"] = u.get("followers", 0)
        stats["created_at"] = u.get("created_at")
    except Exception as e:
        print("user fetch failed:", e)
    try:
        repos = api_get(f"/users/{OWNER}/repos?per_page=100&type=owner", token)
        for r in repos:
            if not r.get("fork"):
                stats["stars"] += r.get("stargazers_count", 0)
            # language bytes per repo (public data)
            try:
                langs = api_get(f"/repos/{OWNER}/{r['name']}/languages", token)
                for k, v in langs.items():
                    stats["langs"][k] = stats["langs"].get(k, 0) + v
            except Exception:
                pass
    except Exception as e:
        print("repos fetch failed:", e)
    try:
        s = api_get(f"/search/commits?q=author:{OWNER}&per_page=1", token)
        stats["commits"] = s.get("total_count")
    except Exception as e:
        print("commit search failed:", e)
    return stats


def account_age(created_at):
    if not created_at:
        return "N/A"
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    months = (now.year - dt.year) * 12 + (now.month - dt.month)
    y, m = divmod(months, 12)
    return f"{y}y {m}m"


def svg_card(title_line, inner_rows, width, height):
    """Common card shell: dark bg, green border, header with blinking cursor."""
    cursor_x = 24 + int(len(title_line) * 7.6)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="{BG}" stroke="{BORDER}" stroke-opacity="0.4" stroke-width="1.5"/>
  <circle cx="24" cy="27" r="4" fill="{HEADER}"/>
  <text x="38" y="32" font-family="{FONT}" font-size="14" fill="{HEADER}">{title_line}</text>
  <text x="{cursor_x}" y="32" font-family="{FONT}" font-size="14" fill="{HEADER}">_</text>
  <line x1="24" y1="46" x2="{width - 24}" y2="46" stroke="{DIM}" stroke-width="2"/>
  {inner_rows}
</svg>'''


def build_stats_svg(s):
    width, height = 480, 212
    rows = [
        ("total_stars", str(s["stars"])),
        ("public_repos", str(s["public_repos"])),
        ("total_commits", f"{s['commits']}+" if s["commits"] is not None else "N/A"),
        ("followers", str(s["followers"])),
        ("account_age", account_age(s["created_at"])),
    ]
    parts = []
    y = 74
    for label, value in rows:
        parts.append(f'<text x="24" y="{y}" font-family="{FONT}" font-size="15" fill="{LABEL}">&gt; {label}:</text>')
        parts.append(f'<text x="{width - 24}" y="{y}" font-family="{FONT}" font-size="15" font-weight="bold" fill="{VALUE}" text-anchor="end">{value}</text>')
        y += 28
    inner = "\n  ".join(parts)
    return svg_card(f"{OWNER}@github:~$ ./stats --live", inner, width, height)


def build_langs_svg(s):
    width, height = 480, 212
    langs = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in langs) or 1
    if not langs:
        inner = f'<text x="24" y="90" font-family="{FONT}" font-size="14" fill="{LABEL}">&gt; no language data available</text>'
        return svg_card(f"{OWNER}@github:~$ ./languages", inner, width, height)

    # stacked bar with rounded clip
    bar_x, bar_y, bar_w, bar_h = 24, 62, width - 48, 14
    segs = []
    x = bar_x
    for i, (name, val) in enumerate(langs):
        w = bar_w * val / total
        color = LANG_COLORS[i % len(LANG_COLORS)]
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{color}"/>')
        x += w
    clip_id = "barclip"
    bar_group = (f'<clipPath id="{clip_id}"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>'
                 f'<g clip-path="url(#{clip_id})">' + "".join(segs) + "</g>")

    # legend: 2 columns x 3 rows
    parts = [bar_group]
    lx, ly = 24, 104
    for i, (name, val) in enumerate(langs):
        col = i % 2
        row = i // 2
        cx = lx + col * 220
        cy = ly + row * 30
        color = LANG_COLORS[i % len(LANG_COLORS)]
        pct = 100.0 * val / total
        parts.append(f'<rect x="{cx}" y="{cy - 11}" width="12" height="12" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{cx + 20}" y="{cy}" font-family="{FONT}" font-size="14" fill="{LABEL}">{name}</text>')
        parts.append(f'<text x="{cx + 190}" y="{cy}" font-family="{FONT}" font-size="14" font-weight="bold" fill="{VALUE}" text-anchor="end">{pct:.1f}%</text>')
    inner = "\n  ".join(parts)
    return svg_card(f"{OWNER}@github:~$ ./languages --by=bytes", inner, width, height)


def main():
    token = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    stats = fetch_stats(token)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "github-stats.svg"), "w", encoding="utf-8") as f:
        f.write(build_stats_svg(stats))
    with open(os.path.join(OUT_DIR, "top-langs.svg"), "w", encoding="utf-8") as f:
        f.write(build_langs_svg(stats))
    print("stats:", {k: v for k, v in stats.items() if k != "langs"})
    print("languages:", sorted(stats["langs"].items(), key=lambda kv: -kv[1])[:6])
    print("SVGs written to", OUT_DIR)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Self-hosted GitHub stats cards (v3 — Matrix terminal surfaces).

Outputs two SVG cards into assets/ (one Matrix-terminal style for BOTH
color schemes — the dark panel is the profile's visual identity):
  github-stats.svg
  top-langs.svg

Design & honesty rules (enforced here, documented in docs/profile-maintenance.md):
  * repos listing is paginated (per_page=100, capped pages)
  * forks are excluded from stars AND from language bytes (consistent policy)
  * language percentages are a share of TOTAL code bytes across the counted
    public non-fork repos — never presented as skill levels
  * the commit number comes from the GitHub commit-search index (public) and
    is labelled as such — it is not claimed to be "every commit ever"
  * API errors never become fake-valid zeros: missing values render as "—"
    and the card footer says "partial data"; if the primary fetches all fail
    the script exits non-zero and the previous SVG files are left untouched
  * every successful generation embeds its UTC timestamp in the card footer
  * file writes are atomic (tmp file + os.replace)

Stdlib only. Env: GH_STATS_TOKEN or GITHUB_TOKEN (raises rate limits).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("STATS_OWNER", "SSSchangerSSS")
OUT_DIR = os.environ.get("STATS_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")

# Repositories whose VENDORED third-party source would drown out the account's
# own code in the byte-based language shares. ShadowHero embeds the LÖVE for
# Android engine tree (C/C++/Shell, ~46 MB — byte-identical profile to the
# already-forked love-android) with the account's own code being the Lua part.
# Excluded from stars AND language bytes alike. Adjust here, document in
# docs/profile-maintenance.md.
EXCLUDED_REPOS = ("SSSchangerSSS/ShadowHero",)

CARD_W, CARD_H = 480, 224
TOP_LANGS = 6
PAGE_SIZE, MAX_PAGES = 100, 10
RETRIES, TIMEOUT = 3, 30

FONT = "ui-monospace, 'Cascadia Code', 'SF Mono', Menlo, Consolas, monospace"

# Matrix terminal surface — same visual family as the banner and the snake
# panel (deep black, phosphor green, thin #123D24 lines). Do not neutralize.
THEME = {
    "bg": "#07110B", "border": "#1E5230", "grid": "#123D24",
    "fg": "#D8FFE5", "muted": "#8BAB96", "dim": "#6E8A78",
    "accent": "#00FF41", "other": "#0D2A18",
    # monochrome green ramp: position encodes rank, not skill
    "langs": ["#00FF41", "#2FE075", "#24B862", "#1B8A4C", "#145C36", "#0F3D24"],
}


# --------------------------------------------------------------- transports --
class FetchError(Exception):
    pass


class RateLimited(FetchError):
    pass


def _attempt(op, retries=RETRIES):
    """Run op() with limited retries on transient failures."""
    last = None
    for attempt in range(retries):
        try:
            return op()
        except RateLimited:
            raise
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                break                     # 4xx: retrying will not help
            if attempt < retries - 1:
                time.sleep(1 + attempt)   # 1s, 2s backoff
    raise FetchError(str(last))


def api_get(path, token):
    """GET a REST endpoint. Raises FetchError/RateLimited."""
    def op():
        req = urllib.request.Request("https://api.github.com" + path)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "stats-card-generator")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.headers.get("X-RateLimit-Remaining") == "0":
                raise RateLimited("rate limit exhausted")
            return json.loads(r.read().decode())
    return _attempt(op)


def graphql(query, token):
    """POST a GraphQL document. Raises FetchError/RateLimited."""
    def op():
        req = urllib.request.Request("https://api.github.com/graphql",
                                     data=json.dumps({"query": query}).encode(),
                                     method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "stats-card-generator")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.headers.get("X-RateLimit-Remaining") == "0":
                raise RateLimited("rate limit exhausted")
            return json.loads(r.read().decode())
    return _attempt(op)


# ------------------------------------------------------------ data pipeline --
def paginate(fetch_page, max_pages=MAX_PAGES):
    """Collect all pages until a short page arrives (or the cap is hit)."""
    items, page = [], 1
    while page <= max_pages:
        chunk = fetch_page(page) or []
        items.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            break
        page += 1
    return items


def aggregate_repos(repos, lang_fetcher, excluded=EXCLUDED_REPOS):
    """Split repositories into honest aggregates.

    Forks and explicitly excluded (vendored-source) repos are excluded
    everywhere. Returns (original_count, stars, lang_bytes, lang_errors).
    lang_fetcher(full_name) -> dict or raises FetchError.
    """
    count, stars, langs, errors = 0, 0, {}, []
    for r in repos:
        if r.get("fork"):
            continue
        if r.get("full_name") in excluded:
            continue
        count += 1
        stars += int(r.get("stargazers_count") or 0)
        try:
            for k, v in (lang_fetcher(r["full_name"]) or {}).items():
                langs[k] = langs.get(k, 0) + int(v)
        except FetchError as e:
            errors.append("%s: %s" % (r.get("name", "?"), e))
    return count, stars, langs, errors


def current_streak(days):
    """Consecutive contribution days ending today (or yesterday if today is 0).

    days: list of ints ordered oldest -> newest. None if no data.
    """
    if days is None:
        return None
    i = len(days) - 1
    if i < 0:
        return 0
    if days[i] == 0 and i > 0:
        i -= 1
    streak = 0
    while i >= 0 and days[i] > 0:
        streak += 1
        i -= 1
    return streak


def lang_rows(langs, top=TOP_LANGS):
    """Top languages with a share-of-TOTAL-bytes percentage, plus 'other'.

    The denominator is the sum of ALL bytes, not just the displayed rows.
    """
    items = sorted(langs.items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in items)
    if total <= 0:
        return [], 0
    rows = [(n, v, 100.0 * v / total) for n, v in items[:top]]
    other = sum(v for _, v in items[top:])
    return rows, other


def account_age(created_at, now=None):
    if not created_at:
        return None
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = now or datetime.now(timezone.utc)
    months = (now.year - dt.year) * 12 + (now.month - dt.month)
    if now.day < dt.day:
        months -= 1
    months = max(months, 0)
    y, m = divmod(months, 12)
    return "%dy %dm" % (y, m) if y else "%dm" % m


def fetch_all(token):
    """Fetch everything; never raises on a single source failing — the
    returned dict records which sources failed in .errors[]."""
    s = {"user": None, "repos": [], "langs": {}, "lang_errors": [],
         "original_repos": 0, "stars": 0, "commits": None, "streak": None,
         "errors": []}

    try:
        s["user"] = api_get("/users/%s" % OWNER, token)
    except FetchError as e:
        s["errors"].append("user: %s" % e)

    try:
        s["repos"] = paginate(
            lambda p: api_get("/users/%s/repos?per_page=%d&type=owner&page=%d"
                              % (OWNER, PAGE_SIZE, p), token))
    except FetchError as e:
        s["errors"].append("repos: %s" % e)

    def lang_fetcher(full_name):
        return api_get("/repos/%s/languages" % full_name, token)

    s["original_repos"], s["stars"], s["langs"], s["lang_errors"] = \
        aggregate_repos(s["repos"], lang_fetcher)
    s["errors"].extend("languages[%s]" % e for e in s["lang_errors"])

    try:
        q = "/search/commits?q=author:%s&per_page=1" % OWNER
        s["commits"] = api_get(q, token).get("total_count")
    except FetchError as e:
        s["errors"].append("commit-search: %s" % e)

    try:
        doc = graphql(
            '{ user(login: "%s") { contributionsCollection { contributionCalendar { '
            'weeks { contributionDays { date contributionCount } } } } } }' % OWNER, token)
        weeks = doc["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
        s["streak"] = current_streak(days)
    except (FetchError, KeyError, TypeError) as e:
        s["errors"].append("calendar: %s" % e)

    return s


# ----------------------------------------------------------------- drawing --
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card_shell(title, subtitle, footer_text):
    t = THEME
    head = (
        '<rect x="24" y="21" width="10" height="10" rx="2" fill="%(accent)s"/>'
        '<text x="42" y="31" font-family="%(font)s" font-size="12" letter-spacing="2" '
        'fill="%(accent)s">%(title)s</text>'
        '<text x="456" y="31" font-family="%(font)s" font-size="10.5" fill="%(muted)s" '
        'text-anchor="end">%(subtitle)s</text>'
        '<line x1="24" y1="46" x2="456" y2="46" stroke="%(grid)s"/>'
        % {"accent": t["accent"], "font": FONT, "muted": t["muted"],
           "grid": t["grid"], "title": esc(title), "subtitle": esc(subtitle)})
    foot = ('<text x="24" y="212" font-family="%(font)s" font-size="9.5" fill="%(dim)s">'
            '%(foot)s</text>'
            % {"font": FONT, "dim": t["dim"], "foot": esc(footer_text)})
    scan = ('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
            '<rect width="4" height="4" fill="%(bg)s"/>'
            '<line x1="0" y1="0" x2="4" y2="0" stroke="%(accent)s" stroke-opacity="0.05"/>'
            '</pattern>'
            % {"bg": t["bg"], "accent": t["accent"]})
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img">'
            '<defs>%s</defs>'
            '<rect x="0.5" y="0.5" width="%d" height="%d" rx="10" fill="url(#scan)" stroke="%s"/>'
            '<rect x="0" y="0" width="4" height="%d" rx="2" fill="%s" fill-opacity="0.85"/>'
            '%s%s%s</svg>'
            % (CARD_W, CARD_H, CARD_W, CARD_H, scan, CARD_W - 1, CARD_H - 1,
               t["border"], CARD_H, t["accent"], head, "{BODY}", foot))


def fmt_val(v):
    if v is None:
        return "—"
    return "{:,}".format(v) if isinstance(v, int) else str(v)


def build_stats_svg(s, stamp, partial):
    t = THEME
    u = s.get("user") or {}
    rows = [
        ("public repos", u.get("public_repos")),
        ("stars · counted repos", s["stars"] if s["repos"] else None),
        ("commits · public search index", s["commits"]),
        ("followers", u.get("followers")),
        ("current streak · days", s["streak"]),
    ]
    body = []
    y = 76
    for label, val in rows:
        body.append('<line x1="24" y1="%d" x2="456" y2="%d" stroke="%s" stroke-opacity="0.5"/>'
                    % (y - 17, y - 17, t["grid"]))
        body.append('<text x="24" y="%d" font-family="%s" font-size="13" fill="%s">%s</text>'
                    % (y, FONT, t["muted"], esc(label)))
        body.append('<text x="456" y="%d" font-family="%s" font-size="14" '
                    'font-weight="600" fill="%s" text-anchor="end">%s</text>'
                    % (y, FONT, t["fg"], esc(fmt_val(val))))
        y += 27
    svg = card_shell("GITHUB — PUBLIC STATS", "@" + OWNER,
                     "%s · %s" % (stamp, "partial data" if partial else "live data"))
    return svg.replace("{BODY}", "".join(body))


def build_langs_svg(s, stamp, partial=False):
    t = THEME
    rows, other = lang_rows(s["langs"])
    body = []
    if not rows:
        body.append('<text x="24" y="120" font-family="%s" font-size="13" fill="%s">'
                    'no language data available yet</text>' % (FONT, t["muted"]))
    else:
        # stacked bar: top langs + other
        bx, by, bw, bh = 24, 64, CARD_W - 48, 12
        total = sum(v for _, v, _ in rows) + other
        segs, x = [], float(bx)
        for i, (name, v, _) in enumerate(rows):
            w = bw * v / total
            segs.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>'
                        % (x, by, w, bh, t["langs"][i % len(t["langs"])]))
            x += w
        if other > 0:
            segs.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>'
                        % (x, by, bx + bw - x, bh, t["other"]))
        body.append('<clipPath id="bar"><rect x="%d" y="%d" width="%d" height="%d" rx="6"/></clipPath>'
                    % (bx, by, bw, bh))
        body.append('<g clip-path="url(#bar)">%s</g>' % "".join(segs))
        # legend: 2 columns x 3 rows
        for i, (name, v, pct) in enumerate(rows):
            col, row = i % 2, i // 2
            cx, cy = 24 + col * 220, 108 + row * 27
            body.append('<rect x="%d" y="%d" width="10" height="10" rx="2" fill="%s"/>'
                        % (cx, cy - 10, t["langs"][i % len(t["langs"])]))
            body.append('<text x="%d" y="%d" font-family="%s" font-size="12.5" fill="%s">%s</text>'
                        % (cx + 18, cy, FONT, t["fg"], esc(name)))
            body.append('<text x="%d" y="%d" font-family="%s" font-size="12.5" '
                        'font-weight="600" fill="%s" text-anchor="end">%.1f%%</text>'
                        % (cx + 202, cy, FONT, t["muted"], pct))
        if other > 0:
            body.append('<text x="244" y="189" font-family="%s" font-size="11" fill="%s">'
                        '+ other languages %.1f%%</text>' % (FONT, t["dim"],
                                                             100.0 * other / total))
    svg = card_shell("CODE — BY BYTES", "@" + OWNER,
                     "share of code bytes · counted public repos · %s%s"
                     % (stamp, " · partial data" if partial else ""))
    return svg.replace("{BODY}", "".join(body))


# -------------------------------------------------------------------- main --
def write_text_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def render_cards(s, out_dir, now=None):
    """Render both Matrix cards; returns list of written paths."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    partial = bool(s["errors"])
    written = []
    for name, builder in (("github-stats", build_stats_svg), ("top-langs", build_langs_svg)):
        p = os.path.join(out_dir, "%s.svg" % name)
        write_text_atomic(p, builder(s, stamp, partial))
        written.append(p)
    return written


def main():
    token = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    s = fetch_all(token)
    primary_failed = (s["user"] is None) and (not s["repos"])
    if primary_failed:
        # Keep the last valid cards on disk; do not publish a fake-looking card.
        print("FATAL: all primary data fetches failed; previous SVGs left untouched",
              file=sys.stderr)
        for e in s["errors"]:
            print("  -", e, file=sys.stderr)
        return 1

    written = render_cards(s, os.path.abspath(OUT_DIR))
    print("user:", bool(s["user"]), "| repos fetched:", len(s["repos"]),
          "| original:", s["original_repos"], "| stars:", s["stars"],
          "| commits:", s["commits"], "| streak:", s["streak"])
    print("errors:", s["errors"] if s["errors"] else "none")
    print("languages:", sorted(s["langs"].items(), key=lambda kv: -kv[1])[:TOP_LANGS])
    for p in written:
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())

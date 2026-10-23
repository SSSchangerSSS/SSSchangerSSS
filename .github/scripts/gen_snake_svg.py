#!/usr/bin/env python3
"""Growing-snake contribution grid generator.

Builds a self-contained animated SVG (SMIL, no JS) of the GitHub contribution
calendar where a real snake slithers over the grid and GROWS every time it
eats a contribution cell. Stdlib only — runs anywhere.

Outputs (GitHub Actions friendly):
  dist/github-contribution-grid-snake.svg        (light palette)
  dist/github-contribution-grid-snake-dark.svg   (dark palette)

Env:
  SNAKE_TOKEN / GITHUB_TOKEN  — token for GraphQL (calendar read)
  SNAKE_OWNER                 — username (default SSSchangerSSS)
  SNAKE_OUT                   — output dir (default dist)
"""
import json
import os
import urllib.request
from datetime import datetime

OWNER = os.environ.get("SNAKE_OWNER", "SSSchangerSSS")
TOKEN = os.environ.get("SNAKE_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OUT_DIR = os.environ.get("SNAKE_OUT", "dist")

CELL, GAP, PAD = 12, 3, 8
STEP_PX = CELL + GAP
MAX_COLS = 53
BASE_LEN = 4      # initial body length (cells)
GROW = 2          # body cells gained per eaten contribution
MAXLEN = 64       # body cap (cells)
FRAME_MS = 28     # per-step duration

PALETTES = {
    "dark": {
        "empty": "#161b22",
        "eaten": "#003b00",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "body": "#00FF41",
        "head": "#8cff9e",
        "eyes": "#05200c",
    },
    "light": {
        "empty": "#ebedf0",
        "eaten": "#cfe6cf",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "body": "#1a7f37",
        "head": "#2ea043",
        "eyes": "#0b2213",
    },
}


def gql(query, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(), method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("User-Agent", "growing-snake-generator")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"])[:300])
    return data


def fetch_cells(owner, token):
    q = ('{ user(login: "%s") { contributionsCollection { contributionCalendar { weeks { '
         'contributionDays { date contributionCount } } } } } }' % owner)
    weeks = gql(q, token)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    cells = {}
    for i, w in enumerate(weeks[:MAX_COLS]):
        for d in w["contributionDays"]:
            dt = datetime.fromisoformat(d["date"]).date()
            cells[(i, dt.isoweekday() % 7)] = int(d["contributionCount"])
    return cells


def level_of(count):
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 4:
        return 2
    if count <= 7:
        return 3
    return 4


def build_path(cells):
    """Serpentine path over active columns (top->bottom, bottom->top ...)."""
    green_cols = [c for (c, r), v in cells.items() if v > 0]
    if not green_cols:
        green_cols = [c for (c, r) in cells]
    c0, c1 = min(green_cols), max(green_cols)
    path = []
    for k, c in enumerate(range(c0, c1 + 1)):
        rows = range(7) if k % 2 == 0 else range(6, -1, -1)
        for r in rows:
            if (c, r) in cells:
                path.append((c, r))
    return path


def center(c, r):
    return (PAD + c * STEP_PX + CELL / 2.0, PAD + r * STEP_PX + CELL / 2.0)


def fmt(x):
    """Format pixel coordinates (0.1px precision is plenty)."""
    s = ("%.1f" % x).rstrip("0").rstrip(".")
    return s if s else "0"


def fkt(x):
    """Format SMIL keyTimes — needs full precision (1e-6) so that
    370-step animations don't quantize to 0.1 and desync from the head."""
    s = ("%.6f" % x).rstrip("0").rstrip(".")
    return s if s else "0"


def generate(palette_name, cells_map, path, STEPS, LENS, path_cols_min, path_cols_max):
    pal = PALETTES[palette_name]
    step_of_cell = {p: i for i, p in enumerate(path)}
    W = PAD * 2 + (path_cols_max - path_cols_min + 1) * STEP_PX - GAP
    H = PAD * 2 + 7 * STEP_PX - GAP
    dur = '%dms' % (STEPS * FRAME_MS)

    parts = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (W, H, W, H))
    parts.append('<title>contribution snake — it grows as it eats!</title>')

    # ---- static grid ----
    grid = []
    for (c, r), v in sorted(cells_map.items()):
        if not (path_cols_min <= c <= path_cols_max):
            continue
        x, y = PAD + c * STEP_PX, PAD + r * STEP_PX
        lvl = pal["levels"][level_of(v)]
        extra = ""
        if v > 0:
            t_eat = step_of_cell.get((c, r))
            if t_eat is not None:
                extra = ('<animate attributeName="fill" values="%s;%s" keyTimes="0;%s" '
                         'calcMode="discrete" dur="%s" repeatCount="indefinite"/>'
                         % (lvl, pal["eaten"], fkt(t_eat / STEPS), dur))
        grid.append('<rect x="%s" y="%s" width="%d" height="%d" rx="2" fill="%s">%s</rect>'
                    % (fmt(x), fmt(y), CELL, CELL, lvl, extra))

    # ---- body segments (discrete visibility windows) ----
    segs = []
    for i in range(1, STEPS):
        x1, y1 = center(*path[i - 1])
        x2, y2 = center(*path[i])
        leave = None
        for t in range(i, STEPS):
            if t - LENS[t] + 1 > i:
                leave = t
                break
        kts = [0, i / STEPS]
        vals = ["0", "1"]
        if leave is not None and leave / STEPS < 1.0:
            kts.append(leave / STEPS)
            vals.append("0")
        segs.append(
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="8.5" '
            'stroke-linecap="round" opacity="0">'
            '<animate attributeName="opacity" values="%s" keyTimes="%s" '
            'calcMode="discrete" dur="%s" repeatCount="indefinite"/></line>'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), pal["body"],
               ";".join(vals), ";".join(fkt(k) for k in kts), dur))

    # ---- head with directional eyes ----
    xs = [fmt(center(*p)[0]) for p in path]
    ys = [fmt(center(*p)[1]) for p in path]
    ex1, ey1, ex2, ey2 = [], [], [], []
    for t, p in enumerate(path):
        if t == 0:
            dx, dy = 1, 0
        else:
            dx = p[0] - path[t - 1][0]
            dy = p[1] - path[t - 1][1]
            if dx == 0 and dy == 0:
                dx, dy = 1, 0
        px, py = center(*p)
        qx, qy = -dy, dx  # perpendicular
        ex1.append(fmt(px + 2.6 * dx + 2.3 * qx))
        ey1.append(fmt(py + 2.6 * dy + 2.3 * qy))
        ex2.append(fmt(px + 2.6 * dx - 2.3 * qx))
        ey2.append(fmt(py + 2.6 * dy - 2.3 * qy))

    head = (
        '<circle cx="%s" cy="%s" r="6.4" fill="%s">'
        '<animate attributeName="cx" values="%s" dur="%s" repeatCount="indefinite" calcMode="discrete"/>'
        '<animate attributeName="cy" values="%s" dur="%s" repeatCount="indefinite" calcMode="discrete"/>'
        '</circle>'
        % (xs[0], ys[0], pal["head"], ";".join(xs), dur, ";".join(ys), dur))
    eyes = ""
    for exl, eyl in ((ex1, ey1), (ex2, ey2)):
        eyes += (
            '<circle cx="%s" cy="%s" r="1.8" fill="%s">'
            '<animate attributeName="cx" values="%s" dur="%s" repeatCount="indefinite" calcMode="discrete"/>'
            '<animate attributeName="cy" values="%s" dur="%s" repeatCount="indefinite" calcMode="discrete"/>'
            '</circle>'
            % (exl[0], eyl[0], pal["eyes"], ";".join(exl), dur, ";".join(eyl), dur))

    parts.append("<g>" + "".join(grid) + "</g>")
    parts.append("<g>" + "".join(segs) + "</g>")
    parts.append(head + eyes)
    parts.append("</svg>")
    return "".join(parts)


def main():
    if not TOKEN:
        raise SystemExit("no token: set SNAKE_TOKEN/GITHUB_TOKEN")
    cells_map = fetch_cells(OWNER, TOKEN)
    path = build_path(cells_map)
    STEPS = len(path)
    cols_used = sorted({c for (c, r) in cells_map})
    path_cols_min = min(c for c, r in path)
    path_cols_max = max(c for c, r in path)

    # body length over time
    LENS, eaten = [], 0
    for p in path:
        if cells_map[p] > 0:
            eaten += 1
        LENS.append(min(MAXLEN, BASE_LEN + GROW * eaten))

    green = sum(1 for p in path if cells_map[p] > 0)
    print("grid cells: %d | snake steps: %d | contribution cells to eat: %d"
          % (len(cells_map), STEPS, green))
    print("body: starts %d, +%d per bite, final %d (cap %d)"
          % (BASE_LEN, GROW, LENS[-1], MAXLEN))

    os.makedirs(OUT_DIR, exist_ok=True)
    for name, pal_name in (("github-contribution-grid-snake.svg", "light"),
                           ("github-contribution-grid-snake-dark.svg", "dark")):
        svg = generate(pal_name, cells_map, path, STEPS, LENS, path_cols_min, path_cols_max)
        out = os.path.join(OUT_DIR, name)
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote %s (%.1f KB, loop %.1fs)"
              % (out, len(svg) / 1024.0, STEPS * FRAME_MS / 1000.0))


if __name__ == "__main__":
    main()

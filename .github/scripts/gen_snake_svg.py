#!/usr/bin/env python3
"""Growing-snake contribution calendar generator (v2 — smooth glide & swell).

Design goals (pure SMIL, no JS — survives GitHub camo):
  * ONE continuous body: the serpentine walk over the grid is a single <path>;
    the snake is an animated stroke-dash window sliding along it, so the body
    glides smoothly cell-to-cell (linear interpolation — no popping segments,
    no teleporting head).
  * REAL GROWTH: on every bite (arrival at a contribution cell) the dash
    length grows by one cell during that step while the dash offset stands
    still — the head advances while the tail pauses, i.e. the snake visibly
    swallows and lengthens. No length cap: final length = every bite kept.
  * REALISM: layered strokes (soft shadow / dark outline / gradient skin /
    light spine), a proper head built from nested translate+rotate groups so
    it pivots naturally into turns, eyes that face the travel direction and a
    flicking forked tongue. A subtle ring pulses on every swallowed cell.

Outputs (GitHub Actions friendly):
  dist/github-contribution-grid-snake.svg        (light palette)
  dist/github-contribution-grid-snake-dark.svg   (dark palette)

CLI:
  python gen_snake_svg.py                     # build both SVGs into $SNAKE_OUT
  python gen_snake_svg.py --frame 8000 --pal dark --png frame.png
                                              # static debug snapshot at t=8s
Env:
  SNAKE_TOKEN / GITHUB_TOKEN  — token for GraphQL (calendar read)
  SNAKE_OWNER                 — username (default SSSchangerSSS)
  SNAKE_OUT                   — output dir (default dist)
"""
import argparse
import json
import os
import urllib.request
from datetime import datetime

OWNER = os.environ.get("SNAKE_OWNER", "SSSchangerSSS")
TOKEN = os.environ.get("SNAKE_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OUT_DIR = os.environ.get("SNAKE_OUT", "dist")

# ---------------------------------------------------------------- geometry --
CELL, GAP, PAD = 12.0, 3.0, 16.0
PITCH = CELL + GAP                      # 15 px between cell centres

# ------------------------------------------------------------------- timing --
BASE_LEN = 3          # body cells at spawn (a little hatchling)
GROW = 1              # body cells gained per swallowed contribution
STEP_MS = 38          # base duration of a one-cell move
BITE_EXTRA_MS = 55    # extra pause when swallowing (the gulp)
LEAD_MS = 600         # hold before the snake enters
TAIL_HOLD_MS = 1200   # hold on the finished snake before the loop restarts

# ------------------------------------------------------------------ palette --
PAL = {
    "dark": {
        "empty": "#161b22",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "outline": "#06451e",
        "skin1": "#0e8f43",
        "skin2": "#4be36e",
        "spine": "#ffffff",
        "spine_op": 0.32,
        "head_stroke": "#06451e",
        "eye": "#eafff0",
        "pupil": "#04180a",
        "tongue": "#ff5b6a",
        "shadow_op": 0.42,
        "gulp": "#8dffab",
    },
    "light": {
        "empty": "#ebedf0",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "outline": "#0b5226",
        "skin1": "#17a349",
        "skin2": "#37d465",
        "spine": "#ffffff",
        "spine_op": 0.5,
        "head_stroke": "#0b5226",
        "eye": "#ffffff",
        "pupil": "#08280f",
        "tongue": "#e8364f",
        "shadow_op": 0.2,
        "gulp": "#1a7f37",
    },
}

BODY_W = 13.5          # outline / shadow stroke width
SKIN_W = 10.0          # skin stroke width
SPINE_W = 3.6          # spine stroke width
HEAD_R = 8.8


# ------------------------------------------------------------------- github --
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
    """Return {(col,row): count}; col 0..52 past->future, row 0=Sunday."""
    q = ('{ user(login: "%s") { contributionsCollection { contributionCalendar { weeks { '
         'contributionDays { date contributionCount } } } } } }' % owner)
    weeks = gql(q, token)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    cells = {}
    for i, w in enumerate(weeks[:53]):
        days = w["contributionDays"]
        days = days + [None] * (7 - len(days))
        for r, d in enumerate(days):
            if d is None:
                continue
            cells[(i, r)] = int(d["contributionCount"])
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


# --------------------------------------------------------------------- path --
def build_path(cells):
    """Serpentine walk row-by-row over the columns that contain any green."""
    if not cells:
        raise ValueError("empty contribution calendar")
    green_cols = sorted({c for (c, r), v in cells.items() if v > 0})
    if not green_cols:
        green_cols = sorted({c for (c, r) in cells})
    c0, c1 = green_cols[0], green_cols[-1]
    path = []
    for k, r in enumerate(range(7)):
        cols = range(c0, c1 + 1) if k % 2 == 0 else range(c1, c0 - 1, -1)
        for c in cols:
            if (c, r) in cells:
                path.append((c, r))
    return path, c0, c1


# ------------------------------------------------------------------- timing --
class Timeline(object):
    """Keyframe table shared by every synced animation.

    Absolute keyframe times: 0, LEAD, LEAD+t(1) .. LEAD+t(N-1), TOT.
    (the first value is duplicated for the lead hold, the last for the tail
    hold — so every list has N+2 entries and linear interpolation never
    skips.)
    """

    def __init__(self, path, cells):
        self.path = path
        self.N = N = len(path)
        self.LEN_PX = PITCH * (N - 1)                    # total path length
        times = [0.0]
        lens = [min(BASE_LEN * PITCH, self.LEN_PX)]
        eaten = 0
        for i in range(1, N):
            step = STEP_MS
            if cells.get(path[i], 0) > 0:
                eaten += 1
                step += BITE_EXTRA_MS
            times.append(times[-1] + step)
            # one cell per bite; never longer than the path itself
            lens.append(min((BASE_LEN + GROW * eaten) * PITCH, self.LEN_PX))
        self.eaten = eaten
        self.head = [PITCH * i for i in range(N)]        # arclength of head
        self.off = [lens[i] - self.head[i] for i in range(N)]   # dash offset
        self.len = lens
        self.times = times                               # move durations
        self.TOT = LEAD_MS + times[-1] + TAIL_HOLD_MS
        # absolute keyframe times (N+2)
        self.kt = [0.0] + [LEAD_MS + t for t in times] + [self.TOT]
        self.kf = [0.0] + [t / self.TOT for t in self.kt[1:]]

    @staticmethod
    def expand(seq):
        """[v0, v1 .. vN-1] -> [v0, v0, v1 .. vN-1, vN-1] (lead+tail holds)."""
        return [seq[0]] + list(seq) + [seq[-1]]

    def keytimes_attr(self):
        return ";".join(fkt(k) for k in self.kf)

    def at(self, t_ms, seq):
        """Value of `seq` (unexpanded, len N) at absolute time t_ms."""
        vals = self.expand(seq)
        kt = self.kt
        if t_ms <= 0:
            return vals[0]
        if t_ms >= kt[-1]:
            return vals[-1]
        lo = max(i for i in range(len(kt)) if kt[i] <= t_ms)
        if lo >= len(kt) - 1:
            return vals[-1]
        u = (t_ms - kt[lo]) / (kt[lo + 1] - kt[lo])
        a, b = vals[lo], vals[lo + 1]
        return a + (b - a) * u


# ------------------------------------------------------------------ formats --
def fmt(x):
    s = "%.2f" % float(x)
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def fkt(x):
    s = "%.6f" % float(x)
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"


# ---------------------------------------------------------------- generator --
def head_angles(path):
    """Unwrapped heading (deg) at each keyframe — the head pivots during the
    move INTO a cell, so it arrives already facing its travel direction."""
    amap = {(1, 0): 0.0, (0, 1): 90.0, (-1, 0): 180.0, (0, -1): 270.0}
    out, prev = [], None
    for i in range(len(path)):
        if i == 0:
            d = (1, 0)
        else:
            d = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        if d not in amap:
            d = (1, 0)
        base = amap[d]
        if prev is None:
            cur = base
        else:
            diff = base - amap[prev]
            if diff > 180:
                diff -= 360
            if diff < -180:
                diff += 360
            cur = out[-1] + diff
        out.append(cur)
        prev = d
    return out


def generate(pal_name, cells, path, c0, tl, freeze_ms=None):
    pal = PAL[pal_name]
    N = tl.N
    ncols = max(c for c, r in path) - c0 + 1
    W = 2 * PAD + ncols * PITCH - GAP
    H = 2 * PAD + 7 * PITCH - GAP
    dur = "%.0fms" % tl.TOT
    kts = tl.keytimes_attr()

    def cx(c):
        return PAD + (c - c0) * PITCH + CELL / 2.0

    def cy(r):
        return PAD + r * PITCH + CELL / 2.0

    # ---------------------------------------------------------- static bits --
    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
               'viewBox="0 0 %s %s" role="img">' % (fmt(W), fmt(H), fmt(W), fmt(H)))
    out.append('<title>growing contribution snake — it swells with every bite</title>')
    out.append('<desc>A snake slithers over the GitHub contribution calendar and '
               'grows one segment for every contribution it eats.</desc>')
    out.append('<defs>')
    out.append('<pattern id="ec" x="%s" y="%s" width="%s" height="%s" '
               'patternUnits="userSpaceOnUse"><rect width="%s" height="%s" rx="2.5" '
               'fill="%s"/></pattern>'
               % (fmt(PAD), fmt(PAD), fmt(PITCH), fmt(PITCH), fmt(CELL), fmt(CELL),
                  pal["empty"]))
    out.append('<linearGradient id="skin" x1="0" y1="0" x2="%s" y2="%s" '
               'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="%s"/>'
               '<stop offset="1" stop-color="%s"/></linearGradient>'
               % (fmt(W), fmt(H), pal["skin1"], pal["skin2"]))
    out.append('</defs>')

    # grid: empty cells via pattern, green cells explicit
    out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="url(#ec)"/>'
               % (fmt(PAD), fmt(PAD), fmt(ncols * PITCH - GAP), fmt(7 * PITCH - GAP)))
    c_max = c0 + ncols - 1
    for (c, r), v in sorted(cells.items()):
        if v <= 0 or not (c0 <= c <= c_max):
            continue
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="2.5" fill="%s"/>'
                   % (fmt(PAD + (c - c0) * PITCH), fmt(PAD + r * PITCH),
                      fmt(CELL), fmt(CELL), pal["levels"][level_of(v)]))

    # gulp rings on every swallowed cell
    out.append(gulp_ring(pal, cells, path, c0, tl, cx, cy, freeze_ms))

    # ------------------------------------------------------------- the body --
    d_attr = "M " + " L ".join(
        "%s %s" % (fmt(cx(c)), fmt(cy(r))) for c, r in path)

    def body_layer(stroke, width, opacity=None, extra=""):
        if freeze_ms is None:
            dash_static = 'stroke-dasharray="%s %s" stroke-dashoffset="%s"' % (
                fmt(tl.len[0]), fmt(tl.LEN_PX), fmt(tl.off[0]))
            anims = (
                '<animate attributeName="stroke-dashoffset" calcMode="linear" '
                'values="%s" keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                % (";".join(fmt(v) for v in tl.expand(tl.off)), kts, dur) +
                '<animate attributeName="stroke-dasharray" calcMode="linear" '
                'values="%s" keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                % (";".join("%s %s" % (fmt(v), fmt(tl.LEN_PX)) for v in tl.expand(tl.len)),
                   kts, dur))
        else:
            dash_static = 'stroke-dasharray="%s %s" stroke-dashoffset="%s"' % (
                fmt(tl.at(freeze_ms, tl.len)), fmt(tl.LEN_PX), fmt(tl.at(freeze_ms, tl.off)))
            anims = ""
        op = ' stroke-opacity="%s"' % fmt(opacity) if opacity is not None else ""
        return ('<path d="%s" transform="%s" fill="none" stroke="%s" stroke-width="%s" '
                'stroke-linecap="round" stroke-linejoin="round" %s%s>%s%s</path>'
                % (d_attr, extra, stroke, fmt(width), dash_static, op, anims, ""))

    out.append(body_layer("#000000", BODY_W, pal["shadow_op"], "translate(2.5 3.5)"))
    out.append(body_layer(pal["outline"], BODY_W))
    out.append(body_layer("url(#skin)", SKIN_W))
    out.append(body_layer(pal["spine"], SPINE_W, pal["spine_op"]))

    # -------------------------------------------------------------- the head --
    ang = head_angles(path)
    xs = [cx(c) for c, r in path]
    ys = [cy(r) for c, r in path]
    if freeze_ms is None:
        tr_vals = ";".join("%s %s" % (fmt(x), fmt(y)) for x, y in
                           zip(tl.expand(xs), tl.expand(ys)))
        ro_vals = ";".join(fmt(a) for a in tl.expand(ang))
        head_anims = (
            '<animateTransform attributeName="transform" type="translate" '
            'calcMode="linear" values="%s" keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
            % (tr_vals, kts, dur))
        rot_anims = (
            '<animateTransform attributeName="transform" type="rotate" '
            'calcMode="linear" values="%s" keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
            % (ro_vals, kts, dur))
        tr_static = "translate(%s %s)" % (fmt(xs[0]), fmt(ys[0]))
        ro_static = "rotate(%s)" % fmt(ang[0])
    else:
        hx = tl.at(freeze_ms, xs)
        hy = tl.at(freeze_ms, ys)
        ha = tl.at(freeze_ms, ang)
        head_anims = rot_anims = ""
        tr_static = "translate(%s %s)" % (fmt(hx), fmt(hy))
        ro_static = "rotate(%s)" % fmt(ha)

    tongue = ('<path d="M 8.2 0 L 13.6 0 M 13.6 0 L 16.8 -2.5 M 13.6 0 L 16.8 2.5" '
              'fill="none" stroke="%s" stroke-width="1.7" stroke-linecap="round" opacity="0">'
              '<animate attributeName="opacity" values="0;0;1;1;0;0" '
              'keyTimes="0;0.42;0.46;0.55;0.6;1" dur="%s" repeatCount="indefinite"/>'
              '</path>' % (pal["tongue"], dur))
    head = (
        '<g transform="%s">%s'
        '<g transform="%s">%s'
        '%s'
        '<circle r="%s" fill="url(#skin)" stroke="%s" stroke-width="2.4"/>'
        '<circle cx="3.4" cy="-4.4" r="2.7" fill="%s"/>'
        '<circle cx="3.4" cy="4.4" r="2.7" fill="%s"/>'
        '<circle cx="4.8" cy="-4.4" r="1.4" fill="%s"/>'
        '<circle cx="4.8" cy="4.4" r="1.4" fill="%s"/>'
        '</g></g>'
        % (tr_static, head_anims, ro_static, rot_anims, tongue,
           fmt(HEAD_R), pal["head_stroke"],
           pal["eye"], pal["eye"], pal["pupil"], pal["pupil"]))
    out.append(head)
    out.append('</svg>')
    return "".join(out)


def gulp_ring(pal, cells, path, c0, tl, cx, cy, freeze_ms):
    """A single ring element that hops (discrete) to every bitten cell and
    pulses (linear) right after each bite."""
    steps = [LEAD_MS + t for t in tl.times]        # absolute arrival times
    foods = [(steps[i], path[i]) for i in range(1, tl.N) if cells.get(path[i], 0) > 0]
    if not foods:
        return ""
    dur = "%.0fms" % tl.TOT

    # discrete cx / cy — needs one value per keyTime: [t=0 anchor] + foods + [t=1 dup]
    first = "%s %s" % (fmt(cx(foods[0][1][0])), fmt(cy(foods[0][1][1])))
    cxk = [0.0] + [min(t / tl.TOT, 1.0) for t, _ in foods]
    cxv = [first] + ["%s %s" % (fmt(cx(c)), fmt(cy(r))) for _, (c, r) in foods]
    cxk.append(1.0)
    cxv.append(cxv[-1])  # duplicate so values count == keyTimes count

    # linear pulse (r + opacity), clamped to stay strictly increasing
    ev = [(0.0, 0.0, 0.0)]
    last_t = 0.0
    for t, (c, r) in foods:
        for dt, rr, oo in ((-0.13, 3.0, 0.0), (0.03, 4.6, 0.85),
                           (0.09, 7.6, 0.55), (0.27, 10.6, 0.0)):
            at = t + dt * 1000.0
            if at <= last_t:
                continue
            last_t = at
            ev.append((min(at / tl.TOT, 1.0), rr, oo))
    ev.append((1.0, 0.0, 0.0))
    if freeze_ms is None:
        r_kt = ";".join(fkt(k) for k, _, _ in ev)
        r_v = ";".join(fmt(rr) for _, rr, _ in ev)
        o_v = ";".join(fmt(oo) for _, _, oo in ev)
        anims = ('<animate attributeName="r" calcMode="linear" values="%s" '
                 'keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                 '<animate attributeName="opacity" calcMode="linear" values="%s" '
                 'keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                 % (r_v, r_kt, dur, o_v, r_kt, dur) +
                 '<animate attributeName="cx" calcMode="discrete" values="%s" '
                 'keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                 '<animate attributeName="cy" calcMode="discrete" values="%s" '
                 'keyTimes="%s" dur="%s" repeatCount="indefinite"/>'
                 % (";".join(cxv), ";".join(fkt(k) for k in cxk), dur,
                    ";".join(cxv), ";".join(fkt(k) for k in cxk), dur))
        static = 'cx="%s" cy="%s" r="0"' % (cxv[0].split()[0], cxv[0].split()[1])
    else:
        anims = ""
        # nearest food at/before freeze time
        past = [(t, c_r) for t, c_r in foods if t <= freeze_ms]
        if past:
            c, r = past[-1][1]
            static = 'cx="%s" cy="%s" r="0"' % (fmt(cx(c)), fmt(cy(r)))
        else:
            static = 'cx="%s" cy="%s" r="0"' % (fmt(cx(path[0][0])), fmt(cy(path[0][1])))
    return ('<circle %s fill="none" stroke="%s" stroke-width="2.2" opacity="0">%s</circle>'
            % (static, pal["gulp"], anims))


# --------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=float, default=None,
                    help="freeze at this many milliseconds (debug snapshot)")
    ap.add_argument("--pal", choices=("dark", "light"), default="dark")
    ap.add_argument("--png", default=None, help="also render the snapshot to PNG")
    ap.add_argument("--out", default=None, help="override output dir")
    args = ap.parse_args()

    if not TOKEN:
        raise SystemExit("no token: set SNAKE_TOKEN/GITHUB_TOKEN")
    try:
        cells = fetch_cells(OWNER, TOKEN)
    except Exception as e:
        raise SystemExit("calendar fetch failed (%s); keeping previous snake output" % e)
    if not cells:
        raise SystemExit("empty contribution calendar; keeping previous snake output")
    path, c0, c1 = build_path(cells)
    tl = Timeline(path, cells)

    bites = tl.eaten
    print("grid: cols %d..%d (%d) x 7 rows = %d cells | steps %d | bites %d"
          % (c0, c1, c1 - c0 + 1, len(cells), tl.N, bites))
    print("body: %d cells (%.0f px) -> %d cells (%.0f px) | loop %.1fs"
          % (BASE_LEN, BASE_LEN * PITCH, tl.len[-1] // PITCH, tl.len[-1],
             tl.TOT / 1000.0))

    if args.frame is not None:
        svg = generate(args.pal, cells, path, c0, tl, freeze_ms=args.frame)
        name = "frame_%s_%dms.svg" % (args.pal, args.frame)
        if args.out:
            name = args.out
        os.makedirs(OUT_DIR, exist_ok=True)
        p = os.path.join(OUT_DIR, name)
        open(p, "w", encoding="utf-8").write(svg)
        print("wrote", p)
        if args.png:
            import cairosvg
            png = os.path.splitext(p)[0] + ".png"
            cairosvg.svg2png(url=p, write_to=png, scale=1.6)
            print("wrote", png)
        return

    os.makedirs(args.out or OUT_DIR, exist_ok=True)
    outdir = args.out or OUT_DIR
    for fname, pal_name in (("github-contribution-grid-snake.svg", "light"),
                            ("github-contribution-grid-snake-dark.svg", "dark")):
        svg = generate(pal_name, cells, path, c0, tl)
        p = os.path.join(outdir, fname)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote %s (%.1f KB)" % (p, len(svg.encode()) / 1024.0))


if __name__ == "__main__":
    main()

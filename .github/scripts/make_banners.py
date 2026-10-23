#!/usr/bin/env python3
"""Generate the Matrix-identity profile banners.

Outputs:
  assets/banner.svg         -- animated Matrix code rain (SMIL only, no JS)
  assets/banner-static.svg  -- frozen-rain fallback (reduced motion / poster)

Identity contract (docs/profile-maintenance.md):
  * deep black surfaces (#020604 / #07110B), phosphor green #00FF41
  * falling code columns with varied speed / length / phase; bright head,
    dim trail; rain is visible from t=0 (negative begin offsets) and loops
    seamlessly (streams enter and exit fully off-canvas)
  * name + title sit on a darker band so they stay readable over the rain
  * system monospace stack only; no external fonts, no scripts,
    no external references, no heavy blur filters (mobile-friendly)
  * deterministic output (seeded RNG) so re-runs never churn the design

Run: python .github/scripts/make_banners.py [--out-dir assets]
"""
import argparse
import os
from random import Random
from xml.sax.saxutils import escape

W, H = 1100, 280
SEED = 20261023

# ---- Matrix palette (the design contract -- do not neutralize) -------------
BG_0 = "#020604"
BG_1 = "#07110B"
GREEN = "#00FF41"
GREEN_SOFT = "#8DFFB0"
TEXT_MAIN = "#D8FFE5"
TEXT_DIM = "#8BAB96"
LINE = "#123D24"

FONT = ("ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, "
        "'DejaVu Sans Mono', monospace")

NAME = "Sohrab Iranpak"
TITLE = "R&D Software Engineer"           # escaped on output
HINTS = "// robotics · MATLAB · .NET · game development"
PROMPT = "$ whoami"
CHROME = "~/profile"

# Half-width katakana + digits + ASCII punctuation: every browser renders
# these from its system fallback fonts -- no font download anywhere.
CHARS = ("ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
         "0123456789<>[]{}=+*/#$%&@!?;:.~^")

GLYPH_SIZE = 14
GLYPH_H = 17
COL_STEP = 26
COL_X0 = 10

BAND_Y0, BAND_Y1 = 78, 206
PANEL_OPACITY = 0.84

NAME_SIZE, TITLE_SIZE, HINT_SIZE, PROMPT_SIZE, CHROME_SIZE = 58, 24, 14, 13, 11
NAME_Y, TITLE_Y, HINT_Y, PROMPT_Y = 148, 180, 197, 98


def build_columns(rng):
    """One deterministic column spec per x position (shared by both files)."""
    cols = []
    x = COL_X0
    while x < W - 8:
        n = rng.randint(8, 20)
        cols.append({
            "x": x,
            "dur": rng.uniform(4.6, 10.5),
            "n": n,
            "soft": rng.random() < 0.24,
            "glyphs": [rng.choice(CHARS) for _ in range(n)],
            "head": rng.choice(CHARS),
        })
        x += COL_STEP
    return cols


def column_group(spec):
    """One rain column: trail glyphs + bright head (no transform/animation)."""
    n = spec["n"]
    trail_col = GREEN_SOFT if spec["soft"] else GREEN
    glyphs = spec["glyphs"]

    parts = []
    for k in range(n - 1):
        frac = (k + 1) / float(n)
        op = 0.05 + 0.60 * (frac ** 1.7)
        parts.append(
            '<text x="0" y="%d" font-size="%d" fill="%s" fill-opacity="%.2f">%s</text>'
            % (k * GLYPH_H, GLYPH_SIZE, trail_col, op, escape(glyphs[k])))
    head_y = (n - 1) * GLYPH_H
    head = escape(spec["head"])
    # cheap halo under the head instead of a blur filter (mobile-friendly)
    parts.append('<text x="0" y="%d" font-size="%d" fill="%s" fill-opacity="0.28">%s</text>'
                 % (head_y, GLYPH_SIZE + 4, GREEN, head))
    parts.append('<text x="0" y="%d" font-size="%d" fill="%s">%s</text>'
                 % (head_y, GLYPH_SIZE, TEXT_MAIN, head))
    return "".join(parts)


def render_column(spec, animate, ty_rng):
    x, n = spec["x"], spec["n"]
    group = column_group(spec)
    if animate:
        begin = -ty_rng.uniform(0.0, spec["dur"])
        anim = ('<animateTransform attributeName="transform" type="translate" '
                'from="0 %.1f" to="0 %d" dur="%.2fs" begin="%.2fs" '
                'repeatCount="indefinite"/>' % (-(n - 1) * GLYPH_H - GLYPH_SIZE,
                                                H, spec["dur"], begin))
        return ('<g transform="translate(%d 0)"><g>%s%s</g></g>' % (x, group, anim))
    # static: freeze mid-fall, always partially inside the canvas
    stream_h = (n - 1) * GLYPH_H + GLYPH_SIZE
    ty = ty_rng.uniform(-stream_h + 60, H - 60)
    return ('<g transform="translate(%d %.1f)" opacity="0.85">%s</g>' % (x, ty, group))


def corner_ticks():
    m, L = 12, 16
    d = []
    for cx, cy, hx, hy in ((m, m, 1, 1), (W - m, m, -1, 1),
                           (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.append("M%d %d h%d M%d %d v%d" % (cx, cy, hx * L, cx, cy, hy * L))
    return ('<path d="%s" stroke="%s" stroke-width="2" fill="none" '
            'stroke-linecap="square" opacity="0.9"/>' % (" ".join(d), GREEN))


def cursor_tspan(animate):
    if animate:
        return ('<tspan fill="%s">_<animate attributeName="opacity" '
                'values="1;0" calcMode="discrete" dur="1.6s" '
                'repeatCount="indefinite"/></tspan>' % GREEN)
    return '<tspan fill="%s">_</tspan>' % GREEN


def build(animate=True):
    rng = Random(SEED)
    ty_rng = Random(SEED + 1)
    cols = [render_column(c, animate, ty_rng) for c in build_columns(rng)]

    name = escape(NAME)
    title = escape(TITLE)
    anim_note = ("Animated Matrix code rain. " if animate
                 else "Static fallback banner (no animation). ")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
  <title>{anim_note}Sohrab Iranpak — R&amp;D Software Engineer</title>
  <desc>{anim_note}Green code columns fall behind a dark terminal panel that reads {escape(NAME)}, {title}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG_0}"/>
      <stop offset="1" stop-color="{BG_1}"/>
    </linearGradient>
    <clipPath id="frame"><rect x="0" y="0" width="{W}" height="{H}" rx="8"/></clipPath>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#bg)"/>

  <g clip-path="url(#frame)" font-family="{FONT}">
{chr(10).join("    " + c for c in cols)}
  </g>

  <!-- readable identity band over the rain -->
  <rect x="0" y="{BAND_Y0}" width="{W}" height="{BAND_Y1 - BAND_Y0}" fill="{BG_0}" fill-opacity="{PANEL_OPACITY}"/>
  <line x1="0" y1="{BAND_Y0}" x2="{W}" y2="{BAND_Y0}" stroke="{LINE}" stroke-width="1"/>
  <line x1="0" y1="{BAND_Y1}" x2="{W}" y2="{BAND_Y1}" stroke="{LINE}" stroke-width="1"/>

  <g font-family="{FONT}" text-anchor="middle">
    <text x="550" y="{PROMPT_Y}" font-size="{PROMPT_SIZE}" letter-spacing="1" fill="{TEXT_DIM}">{escape(PROMPT)}</text>
    <text x="550" y="{NAME_Y}" font-size="{NAME_SIZE}" font-weight="700" fill="{GREEN}" opacity="0.20">{name}<tspan fill="{GREEN}">_</tspan></text>
    <text x="550" y="{NAME_Y}" font-size="{NAME_SIZE}" font-weight="700" fill="{TEXT_MAIN}">{name}{cursor_tspan(animate)}</text>
    <text x="550" y="{TITLE_Y}" font-size="{TITLE_SIZE}" letter-spacing="3" fill="{GREEN}">{title}</text>
    <text x="550" y="{HINT_Y}" font-size="{HINT_SIZE}" fill="{TEXT_DIM}">{escape(HINTS)}</text>
  </g>

  <text x="16" y="26" font-family="{FONT}" font-size="{CHROME_SIZE}" fill="{TEXT_DIM}" opacity="0.9">{escape(CHROME)}</text>
  {corner_ticks()}

  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="8" fill="none" stroke="{LINE}" stroke-width="1.5"/>
</svg>
'''


def write_banners(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for fname, animate in (("banner.svg", True), ("banner-static.svg", False)):
        p = os.path.join(out_dir, fname)
        with open(p, "w", encoding="utf-8") as f:
            f.write(build(animate))
        written.append(p)
        print("wrote", p)
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
    args = ap.parse_args()
    write_banners(os.path.abspath(args.out_dir))


if __name__ == "__main__":
    main()

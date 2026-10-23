#!/usr/bin/env python3
"""Generate the static profile banners (light + dark) from one geometry.

Design rules (see docs/profile-maintenance.md):
  * static — no SMIL/CSS animation, no scripts, no external refs
  * system monospace stack only (no font downloads)
  * neutral surfaces matching GitHub, single controlled emerald accent
  * thin blueprint grid + subtle robotics / game-dev line motifs
  * text is duplicated as real text in README.md / README.fa.md

Output: assets/banner-light.svg, assets/banner-dark.svg
Run:    python .github/scripts/make_banners.py [--out-dir assets]
"""
import argparse
import os

W, H = 1000, 150
PAD_X = 44

THEMES = {
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "grid": "#1f2328", "grid_op": 0.045,
        "name": "#1f2328", "tagline": "#57606a", "accent": "#0e8a4d",
        "line": "#d8dee4", "motif": "#c7d1da", "tick": "#d0d7de",
    },
    "dark": {
        "bg": "#0d1117", "border": "#21262d", "grid": "#ffffff", "grid_op": 0.035,
        "name": "#e6edf3", "tagline": "#7d8590", "accent": "#10b981",
        "line": "#21262d", "motif": "#30363d", "tick": "#21262d",
    },
}

NAME = "SOHRAB IRANPAK"
TAGLINE = "R&amp;D SOFTWARE ENGINEER"   # & escaped for XML
NAME_SIZE, TAG_SIZE = 38, 15
NAME_LS, TAG_LS = 3, 5

GRID_STEP = 50


def grid_path():
    d = []
    for x in range(GRID_STEP, W, GRID_STEP):
        d.append("M%d 0V%d" % (x, H))
    for y in range(GRID_STEP, H, GRID_STEP):
        d.append("M0 %dH%d" % (y, W))
    return " ".join(d)


def ruler_ticks(t, y):
    """Small engineering-drawing ticks under the tagline."""
    seg, x = [], PAD_X
    while x <= PAD_X + 330:
        seg.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>'
                   % (x, y, x, y + (7 if (x - PAD_X) % 100 == 0 else 4), t["tick"]))
        x += 25
    return "".join(seg)


def robot_arm(t):
    """Line-art robot arm motif (three joints, gripper) + circuit trace."""
    g = ['<g stroke="%s" stroke-width="2" fill="none" stroke-linecap="round">' % t["motif"]]
    g.append('<rect x="812" y="116" width="44" height="7" rx="2" fill="%s" stroke="none"/>' % t["motif"])
    g.append('<line x1="834" y1="116" x2="834" y2="96"/>')
    g.append('<line x1="834" y1="96" x2="858" y2="70"/>')
    g.append('<line x1="858" y1="70" x2="886" y2="80"/>')
    g.append('<path d="M886 80 l10 -5 M886 80 l11 4"/>')
    for jx, jy in ((834, 96), (858, 70), (886, 80)):
        g.append('<circle cx="%d" cy="%d" r="3.2" fill="%s" stroke="none"/>'
                 % (jx, jy, t["accent"]))
    g.append('<path d="M886 80 H926 l8 8 H1000" stroke-width="1.2" stroke="%s"/>' % t["motif"])
    g.append('<circle cx="926" cy="80" r="2" fill="%s" stroke="none"/>' % t["accent"])
    g.append("</g>")
    return "".join(g)


def dpad(t):
    """Small game d-pad motif."""
    return ('<g stroke="%s" stroke-width="2.4" fill="none" stroke-linecap="round" '
            'stroke-linejoin="round">'
            '<path d="M952 96 v20 M942 106 h20"/>'
            '</g>'
            '<circle cx="952" cy="106" r="2.6" fill="%s"/>'
            % (t["motif"], t["accent"]))


def banner(theme):
    t = THEMES[theme]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
  <title>Sohrab Iranpak — R&amp;D Software Engineer</title>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t['bg']}" stroke="{t['border']}"/>
  <path d="{grid_path()}" stroke="{t['grid']}" stroke-opacity="{t['grid_op']}" stroke-width="1" fill="none"/>
  <path d="M0 128 H{W}" stroke="{t['line']}" stroke-width="1" fill="none"/>

  <!-- identity block -->
  <rect x="{PAD_X}" y="38" width="4" height="58" rx="2" fill="{t['accent']}"/>
  <text x="{PAD_X + 22}" y="72" font-family="ui-monospace, 'Cascadia Code', 'SF Mono', Menlo, Consolas, monospace"
        font-size="{NAME_SIZE}" font-weight="700" letter-spacing="{NAME_LS}" fill="{t['name']}">{NAME}</text>
  <text x="{PAD_X + 23}" y="104" font-family="ui-monospace, 'Cascadia Code', 'SF Mono', Menlo, Consolas, monospace"
        font-size="{TAG_SIZE}" letter-spacing="{TAG_LS}" fill="{t['tagline']}">{TAGLINE}</text>
  {ruler_ticks(t, 114)}

  <!-- motifs -->
  {robot_arm(t)}
  {dpad(t)}
</svg>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
    args = ap.parse_args()
    out = os.path.abspath(args.out_dir)
    os.makedirs(out, exist_ok=True)
    for theme in ("light", "dark"):
        p = os.path.join(out, "banner-%s.svg" % theme)
        with open(p, "w", encoding="utf-8") as f:
            f.write(banner(theme))
        print("wrote", p)


if __name__ == "__main__":
    main()

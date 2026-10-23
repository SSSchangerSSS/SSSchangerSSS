#!/usr/bin/env python3
"""Theme the Platane/snk output as a Matrix terminal panel.

The snk engine computes the snake path/animation from the real contribution
calendar; this script ONLY themes its SVG output:

  * injects the deep-black panel background (#07110B) so the calendar reads
    as a Matrix panel on both GitHub light and dark themes (the engine's
    own output has a transparent background);
  * draws a 1px border around the panel -- stronger on the light-page
    variant so the panel edge survives a white background;
  * validates the result as XML and writes atomically.

It never modifies the animation, the geometry or the data. If the input is
not a parseable SVG with usable dimensions, it exits non-zero and leaves the
previous file untouched.

Run:  python .github/scripts/theme_snake_svg.py [--dir dist]
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

MARK = "matrix-panel-bg"

# variant -> (panel bg, border)
THEMES = {
    "light": {"bg": "#07110B", "border": "#2E5A3C"},
    "dark": {"bg": "#07110B", "border": "#123D24"},
}


def _num(v):
    """'824' / '824px' -> 824.0, else None."""
    if v is None:
        return None
    v = v.strip()
    if v.endswith("px"):
        v = v[:-2]
    try:
        return float(v)
    except ValueError:
        return None


def dims(root):
    """Width/height from attributes, falling back to the viewBox."""
    w, h = _num(root.get("width")), _num(root.get("height"))
    if w and h:
        return w, h
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    if len(vb) == 4:
        try:
            return float(vb[2]), float(vb[3])
        except ValueError:
            pass
    return None, None


def theme_file(path, variant):
    """Inject the Matrix panel into one SVG file (idempotent, atomic)."""
    if variant not in THEMES:
        raise SystemExit("unknown variant: %s" % variant)
    pal = THEMES[variant]
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise SystemExit("not valid XML, leaving %s untouched: %s" % (path, e))
    root = tree.getroot()
    if root.tag != "{%s}svg" % SVG_NS:
        raise SystemExit("not an SVG document: %s" % path)

    w, h = dims(root)
    if not w or not h:
        raise SystemExit("no usable width/height/viewBox in %s; "
                         "leaving previous output untouched" % path)

    # idempotence: never stack a second panel on an already-themed file
    for el in list(root):
        if el.get("id") == MARK:
            print("already themed, skip", path)
            return

    ns = "{%s}" % SVG_NS
    bg = ET.Element(ns + "rect", {
        "id": MARK, "x": "0", "y": "0",
        "width": "%g" % w, "height": "%g" % h, "fill": pal["bg"]})
    border = ET.Element(ns + "rect", {
        "x": "0.5", "y": "0.5", "width": "%g" % (w - 1), "height": "%g" % (h - 1),
        "fill": "none", "stroke": pal["border"], "stroke-width": "1"})
    root.insert(0, bg)
    root.append(border)

    tmp = path + ".tmp"
    tree.write(tmp, encoding="unicode")
    try:
        ET.parse(tmp)                      # the output must be valid XML
    except ET.ParseError as e:
        os.unlink(tmp)
        raise SystemExit("themed output failed validation, %s untouched: %s"
                         % (path, e))
    os.replace(tmp, path)
    print("themed", path, "->", variant)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="dist")
    args = ap.parse_args()
    targets = (
        ("github-contribution-grid-snake.svg", "light"),
        ("github-contribution-grid-snake-dark.svg", "dark"),
    )
    for fname, variant in targets:
        p = os.path.join(args.dir, fname)
        if not os.path.exists(p):
            raise SystemExit("missing snk output %s; keeping previous output"
                             % p)
        theme_file(p, variant)


if __name__ == "__main__":
    main()

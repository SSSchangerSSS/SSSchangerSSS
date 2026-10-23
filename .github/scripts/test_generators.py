#!/usr/bin/env python3
"""Unit tests for the profile SVG generators (stdlib unittest only).

Everything here runs on SYNTHETIC fixture data inside temp directories.
Test artifacts are never written to assets/ and never published — the
network-dependent functions (fetch_*, api_get, graphql) are intentionally
NOT covered here; they are exercised by the GitHub Actions runs themselves.

Run:  python .github/scripts/test_generators.py
"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_snake_svg as snake        # noqa: E402
import gen_stats_svg as stats        # noqa: E402


def make_cells(cols, rows=7, value_fn=None, col_offset=0):
    """Synthetic contribution calendar: cells[(col, row)] = count."""
    value_fn = value_fn or (lambda c, r: (c + r) % 3)
    return {(c, r): value_fn(c, r)
            for c in range(col_offset, col_offset + cols)
            for r in range(rows)}


def animates(doc):
    return (doc.getElementsByTagName("animate") +
            doc.getElementsByTagName("animateTransform"))


def check_smil(doc, testcase):
    """values/keyTimes counts match, times strictly increase, span [0, 1]."""
    for a in animates(doc):
        vals = a.getAttribute("values").split(";")
        kts = a.getAttribute("keyTimes").split(";")
        testcase.assertEqual(len(vals), len(kts),
                             "count mismatch on %s" % a.getAttribute("attributeName"))
        kt = [float(x) for x in kts]
        for i in range(len(kt) - 1):
            testcase.assertLess(kt[i], kt[i + 1], "non-monotonic keyTimes")
        if a.getAttribute("calcMode") == "discrete":
            testcase.assertAlmostEqual(kt[0], 0.0)
        else:
            testcase.assertAlmostEqual(kt[0], 0.0)
            testcase.assertAlmostEqual(kt[-1], 1.0)


class SnakeGeometryTests(unittest.TestCase):
    def test_offset_columns_geometry(self):
        """Width/viewBox must track the ACTIVE column span, not assume col 0."""
        cells = make_cells(cols=8, col_offset=5)
        path, c0, c1 = snake.build_path(cells)
        self.assertEqual(c0, 5)
        self.assertEqual(c1, 12)
        tl = snake.Timeline(path, cells)
        svg = snake.generate("dark", cells, path, c0, tl)
        doc = minidom.parseString(svg)
        root = doc.documentElement
        ncols = c1 - c0 + 1
        self.assertEqual(float(root.getAttribute("width")),
                         2 * snake.PAD + ncols * snake.PITCH - snake.GAP)
        # every green rect must sit inside the shifted grid area
        for rect in doc.getElementsByTagName("rect"):
            fill = rect.getAttribute("fill")
            if fill.startswith("#") and fill != snake.PAL["dark"]["empty"]:
                self.assertGreaterEqual(float(rect.getAttribute("x")), snake.PAD)

    def test_head_equals_body_tip_at_keyframes(self):
        """The head translation and the dash tip must share one coordinate model."""
        cells = make_cells(cols=12, col_offset=3)
        path, c0, _ = snake.build_path(cells)
        tl = snake.Timeline(path, cells)
        for i in range(tl.N):
            self.assertAlmostEqual(tl.len[i] - tl.off[i], snake.PITCH * i, places=6)
        # and mid-move interpolation keeps them equal too
        for t_ms in (900, 2500, 6000, 12000):
            self.assertAlmostEqual(tl.at(t_ms, tl.len) - tl.at(t_ms, tl.off),
                                   tl.at(t_ms, tl.head), places=4)

    def test_growth_on_bite_steps_only(self):
        cells = make_cells(cols=6, value_fn=lambda c, r: 1 if (c % 2 == 0) else 0,
                           col_offset=0)
        path, _, _ = snake.build_path(cells)
        tl = snake.Timeline(path, cells)
        grows = sum(1 for i in range(1, tl.N) if tl.len[i] > tl.len[i - 1])
        bites = sum(1 for i in range(1, tl.N) if cells[path[i]] > 0)
        self.assertEqual(grows, bites)
        self.assertGreater(grows, 0)

    def test_length_clamped_on_short_path(self):
        """A nearly-all-green tiny grid must not push the dash past the path."""
        cells = make_cells(cols=2, value_fn=lambda c, r: 0 if (c == 0 and r == 0) else 5)
        path, _, _ = snake.build_path(cells)
        tl = snake.Timeline(path, cells)
        self.assertLessEqual(tl.len[-1], tl.LEN_PX)

    def test_all_zero_calendar_still_renders(self):
        cells = make_cells(cols=10, value_fn=lambda c, r: 0)
        path, _, _ = snake.build_path(cells)
        tl = snake.Timeline(path, cells)
        self.assertEqual(tl.eaten, 0)
        for pal in ("light", "dark"):
            doc = minidom.parseString(snake.generate(pal, cells, path, path[0][0], tl))
            check_smil(doc, self)

    def test_empty_calendar_is_rejected(self):
        with self.assertRaises(ValueError):
            snake.build_path({})

    def test_both_variants_valid_with_synced_timing(self):
        cells = make_cells(cols=20, col_offset=7)
        path, c0, _ = snake.build_path(cells)
        tl = snake.Timeline(path, cells)
        for pal in ("light", "dark"):
            doc = minidom.parseString(snake.generate(pal, cells, path, c0, tl))
            check_smil(doc, self)
        # the synced animates (dashoffset/dasharray × 4 layers + head
        # translate + rotate) must all share ONE keyTimes string
        synced = tuple(a.getAttribute("keyTimes") for a in animates(doc)
                       if a.getAttribute("attributeName") in
                       ("stroke-dashoffset", "stroke-dasharray", "transform"))
        self.assertGreaterEqual(len(synced), 10)
        self.assertEqual(len(set(synced)), 1)
        synced_dark = tuple(a.getAttribute("keyTimes") for a in animates(doc)
                            if a.getAttribute("attributeName") in
                            ("stroke-dashoffset", "stroke-dasharray", "transform"))
        self.assertEqual(synced, synced_dark)


class StatsLogicTests(unittest.TestCase):
    def test_aggregate_excludes_forks_consistently(self):
        repos = [
            {"full_name": "o/a", "name": "a", "fork": False, "stargazers_count": 2},
            {"full_name": "o/f", "name": "f", "fork": True, "stargazers_count": 500},
            {"full_name": "o/b", "name": "b", "fork": False, "stargazers_count": 1},
        ]
        fake_langs = {"o/a": {"Python": 10}, "o/b": {"Lua": 5}}
        count, stars, langs, errors = stats.aggregate_repos(
            repos, lambda fn: fake_langs[fn])
        self.assertEqual((count, stars), (2, 3))          # fork star ignored
        self.assertEqual(langs, {"Python": 10, "Lua": 5})  # fork bytes ignored
        self.assertEqual(errors, [])

    def test_lang_percentage_denominator_is_total(self):
        rows, other = stats.lang_rows({"A": 60, "B": 30, "C": 10}, top=2)
        self.assertEqual([(r[0], round(r[2], 1)) for r in rows], [("A", 60.0), ("B", 30.0)])
        self.assertEqual(other, 10)

    def test_lang_rows_empty(self):
        rows, other = stats.lang_rows({})
        self.assertEqual((rows, other), ([], 0))

    def test_current_streak(self):
        self.assertEqual(stats.current_streak([0, 0, 3, 1, 0, 2, 2, 0]), 2)
        self.assertEqual(stats.current_streak([0, 0, 0, 3, 1, 2, 2]), 4)
        self.assertEqual(stats.current_streak([0] * 10), 0)
        self.assertIsNone(stats.current_streak(None))
        self.assertEqual(stats.current_streak([]), 0)

    def test_account_age(self):
        created = "2025-03-15T00:00:00Z"
        self.assertEqual(stats.account_age(created, datetime(2026, 10, 23,
                                                             tzinfo=timezone.utc)),
                         "1y 7m")
        self.assertIsNone(stats.account_age(None))

    def test_fmt_val_marks_missing_data(self):
        self.assertEqual(stats.fmt_val(None), "—")
        self.assertEqual(stats.fmt_val(0), "0")     # a real zero stays a zero
        self.assertEqual(stats.fmt_val(12345), "12,345")

    def test_render_cards_atomic_and_valid(self):
        s = {"user": {"public_repos": 4, "followers": 3,
                      "created_at": "2025-03-15T00:00:00Z"},
             "repos": [{"fork": False}] * 4, "langs": {"C#": 70, "Lua & LuaJIT": 30},
             "lang_errors": [], "original_repos": 4, "stars": 2, "commits": 99,
             "streak": 5, "errors": []}
        with tempfile.TemporaryDirectory() as tmp:
            written = stats.render_cards(s, tmp,
                                         datetime(2026, 10, 23, 11, 43,
                                                  tzinfo=timezone.utc))
            self.assertEqual(len(written), 4)
            for p in written:
                self.assertTrue(os.path.exists(p))
                self.assertFalse(os.path.exists(p + ".tmp"))
                doc = minidom.parse(p)          # valid XML
                check_smil = None               # noqa: F841 (cards have no SMIL)
                texts = " ".join(t.firstChild.nodeValue for t in doc.getElementsByTagName("text")
                                 if t.firstChild)
                self.assertIn("2026-10-23 11:43 UTC", texts)
            # a second render must atomically replace, not append/corrupt
            stats.render_cards(s, tmp)
            for p in written:
                minidom.parse(p)

    def test_escape_of_special_characters(self):
        s = {"user": None, "repos": [], "langs": {}, "lang_errors": [],
             "original_repos": 0, "stars": 0, "commits": None, "streak": None,
             "errors": ["user: simulated outage"]}
        with tempfile.TemporaryDirectory() as tmp:
            stats.render_cards(s, tmp)
            dark = minidom.parse(os.path.join(tmp, "github-stats-dark.svg"))
            texts = " ".join(t.firstChild.nodeValue for t in dark.getElementsByTagName("text")
                             if t.firstChild)
            self.assertIn("partial data", texts)
            self.assertIn("—", texts)          # missing values are honest
        langs_svg = stats.build_langs_svg(
            {"user": None, "repos": [], "langs": {"X&Y": 5}, "lang_errors": [],
             "original_repos": 0, "stars": 0, "commits": None, "streak": None,
             "errors": []}, "dark", "stamp")
        self.assertIn("X&amp;Y", langs_svg)

    def test_paginate_stops_at_short_page(self):
        calls = []

        def fetch_page(p):
            calls.append(p)
            return [{"i": 1}] * (stats.PAGE_SIZE if p == 1 else 3)

        self.assertEqual(len(stats.paginate(fetch_page)), stats.PAGE_SIZE + 3)
        self.assertEqual(calls, [1, 2])

    def test_paginate_respects_cap(self):
        calls = []

        def fetch_page(p):
            calls.append(p)
            return [{"i": 1}] * stats.PAGE_SIZE

        stats.paginate(fetch_page)
        self.assertEqual(calls, list(range(1, stats.MAX_PAGES + 1)))


if __name__ == "__main__":
    unittest.main(verbosity=2)

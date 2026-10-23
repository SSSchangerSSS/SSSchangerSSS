# Profile Maintenance Guide

How to keep this profile working and how to change it safely. Everything here
refers to files inside this repository (`SSSchangerSSS/SSSchangerSSS`).

## The design contract (read before editing)

The profile identity is **Matrix**: deep black surfaces (`#020604`/`#07110B`),
phosphor green (`#00FF41`), soft green accents (`#8DFFB0`), body text
(`#D8FFE5`/`#8BAB96`) and thin `#123D24` lines. The banner, the snake panel
and both stat cards are one visual family. Do not neutralize the palette,
do not replace the animated banner with a static corporate one, and do not
hide the snake in a `<details>` block — those were tried and reverted.
Professionalism here = proportion, readability, correct motion and
consistency, not the absence of Matrix.

## Repository map

| Path | What it is | Regenerated? |
|---|---|---|
| `README.md` / `README.fa.md` | Profile content (English / Persian) | manual |
| `assets/banner.svg` | Animated Matrix code-rain banner (SMIL, no JS) | `make_banners.py` |
| `assets/banner-static.svg` | Frozen-rain fallback (reduced motion / poster) | `make_banners.py` |
| `assets/github-stats.svg`, `assets/top-langs.svg` | Matrix-terminal stat cards | `gen_stats_svg.py` (daily) |
| `.github/scripts/make_banners.py` | Banner source (deterministic, seeded RNG) | — |
| `.github/scripts/gen_stats_svg.py` | Stats card generator | — |
| `.github/scripts/theme_snake_svg.py` | Adds the Matrix panel to the snk output | — |
| `.github/scripts/test_generators.py` | Stdlib unit tests for all of the above | — |
| `.github/workflows/stats.yml` | Daily stats regeneration (01:30 UTC) + push/dispatch | — |
| `.github/workflows/snake.yml` | Daily snake regeneration (00:00 UTC) + push/dispatch, publishes to the `output` branch | — |
| `output` branch | Hosts the two snake SVGs the READMEs embed | CI |

> History note (2026-10-23): the snake used to be a custom generator
> (`gen_snake_svg.py`). It never truly *ate* cells and swept every row of a
> truncated calendar. It was replaced by the proven **Platane/snk** engine
> (svg-only edition) with a Matrix palette; the old generator and its tests
> were removed **with** that migration, not silently.

## Common changes

### Intro, projects, contact
Edit `README.md` and keep `README.fa.md` in sync (and vice versa). Both files
must list the same projects in the same order and keep the section order:
banner → terminal intro → Contribution Matrix → projects → tools → stats →
EOF line. Do not add contact channels you have not verified; when you are
ready to publish an email or LinkedIn, add a line to the end of both READMEs.
Leave a blank line between HTML blocks and Markdown headings/lists, otherwise
GitHub renders the raw tags as text.

### Banner (colors, speed, density, text)
All knobs are constants at the top of `.github/scripts/make_banners.py`:
`BG_0/BG_1` (surface), `GREEN/GREEN_SOFT` (rain), `TEXT_MAIN/TEXT_DIM/LINE`,
`NAME/TITLE/HINTS`, `GLYPH_H`/`COL_STEP` (density), stream speed inside
`build_columns()` (`dur` range). Then run:

```bash
python .github/scripts/make_banners.py
```

This rewrites `assets/banner.svg` and `assets/banner-static.svg` from the
same seeded geometry (output is deterministic — same seed, same pixels).
Commit both files and bump the `?v=` on the banner URLs in both READMEs.

Rules that keep it working on GitHub:
- the banner is a **black Matrix panel in both color schemes** — that is
  intentional and explicitly wanted; only adjust borders/contrast if needed;
- SMIL animation only (no JS, no `<script>`, no `foreignObject`, no external
  fonts — the glyph set renders from system font fallbacks);
- rain must be visible at load time (negative `begin` offsets) and loop
  without a visible pop (streams start fully above / exit fully below);
- the name/title sit on the darker band and are repeated as real text in the
  READMEs below the banner;
- keep the `<picture>` reduced-motion fallback in the READMEs pointing at
  `assets/banner-static.svg`.

### Snake (engine, palette, panel)
Engine: **[Platane/snk `svg-only@v3`](https://github.com/Platane/snk)** — it
reads the real contribution calendar, computes a purposeful path over the
contributed cells, consumes each cell as the snake passes (an eaten cell
stays dark until the cycle restarts), keeps the full 52-week grid with
correct weekday alignment, and grows the body while eating. Growth rate and
speed are engine-defined; there are no hidden knobs for them in the API —
do not invent query params that do not exist (documented options are
`palette`, `color_snake`, `color_dots`, `color_background` for gif only).

Colors live in `.github/workflows/snake.yml` on the `outputs:` query string:
`color_snake=%2300FF41` and `color_dots=` with exactly five URL-encoded hex
values (`%23...`, first = empty cell). The panel background and border are
added afterwards by `.github/scripts/theme_snake_svg.py` (snk has no
background option for SVG; `theme_snake_svg.py` injects `#07110B` plus a
`#123D24` border for the dark variant and a stronger `#2E5A3C` border for
the light-page variant, then re-validates the XML and writes atomically).

Filenames (`github-contribution-grid-snake.svg`,
`github-contribution-grid-snake-dark.svg`) and the `output` branch are part
of the README contract — change them only together with the READMEs and this
workflow. If GitHub's image cache ever serves a stale snake, bump the `?v=`
on the snake URLs in both READMEs.

If the snk run or the theming step fails, the workflow fails and the
previous day's SVGs stay on the `output` branch — no fake calendar is ever
published. Keep it that way.

### Stats card colors & content
Colors live in `THEME` in `.github/scripts/gen_stats_svg.py` (one
Matrix-terminal surface for both color schemes). Rows live in
`build_stats_svg()`; the language bar/legend lives in `build_langs_svg()`.
Honesty rules you must keep when editing:

- forks stay excluded from stars **and** language bytes (`aggregate_repos`);
- repos with vendored third-party engine trees stay excluded too
  (`EXCLUDED_REPOS` in the script; currently `SSSchangerSSS/ShadowHero`,
  which embeds the LÖVE-for-Android engine source and would otherwise
  drown the language card in ~46 MB of C/C++ that is not the account's
  own code). Add or remove entries there and note the change in the
  commit message;
- language percentages always divide by **all** counted bytes
  (`lang_rows`), never by the displayed rows only, and are never
  presented as skill levels;
- the commit row keeps its "public search index" label — it reflects
  `GET /search/commits?q=author:<user>`, not every commit ever made;
- missing values render as `—` with a "partial data" footer — never as
  fabricated zeros (`fmt_val`);
- if user+repos fetches both fail, the script exits non-zero and the previous
  SVGs stay untouched (do not remove that guard);
- keep writes atomic (`write_text_atomic`) so CI never publishes half a file;
- the cards are static on purpose — motion stays in the banner and the snake.

### Schedules
Cron times live in the two workflow files. `snake.yml` runs at 00:00 UTC,
`stats.yml` at 01:30 UTC (deliberately staggered; both also run on pushes to
`main` and on manual dispatch). Both workflows are pinned to
`contents: write` only, run the generator tests first, use `concurrency`
groups, and use the built-in `GITHUB_TOKEN` (the snk action uses the token
the runner injects automatically). Never add another token to these files.

## Running things locally

```bash
# tests (no network needed, uses synthetic data)
python .github/scripts/test_generators.py

# banners
python .github/scripts/make_banners.py

# stats cards (reads live GitHub data)
GH_STATS_TOKEN=<token> python .github/scripts/gen_stats_svg.py

# snake theming dry-run on an snk SVG you placed in dist/
python .github/scripts/theme_snake_svg.py --dir dist
```

Any personal access token with public read access is enough for local runs;
CI uses the built-in `GITHUB_TOKEN`. Never commit a token or put one in a
URL — `test_generators.py` scans the repo text files for token patterns.

## Manual account settings (not done via README)

These are GitHub UI settings — the README cannot change them:

- **Profile bio suggestion:**
  `R&D Software Engineer — robotics simulation (MATLAB), .NET (WPF/MVVM), and game development.`
- **Suggested pinned repositories (in this order):**
  1. `The-Great-Rostam` — playable browser game, has a live demo
  2. `3degree_RRR_robot_in_matlab_genetic_algorithm` — MATLAB robotics + GA
  3. `MVVM_WPF_Car_Rental_Management_App` — full-stack WPF/MVVM discipline
  4. `2d_lua_game_made_with_love2d_engine_for_android` — Lua/LÖVE 2D on Android

## Acceptance checklist for future edits

- every file referenced from the READMEs exists (`RepoConsistencyTests` in
  `test_generators.py` guards this — run it);
- all SVGs parse as XML (e.g. `python -c "from xml.dom import minidom;
  minidom.parse('<file>')"`); the snake panel keeps its `id="matrix-panel-bg"`
  background exactly once;
- the profile reads as Matrix at first glance in **both** GitHub color
  schemes; the banner stays a black panel on light mode;
- checked at ~375 px width: nothing breaks, banner name still readable;
- the main content (name, intro, projects, links) is understandable with all
  images blocked;
- no fabricated numbers are published (stars, commits, skills, years...);
- rerunning both generators and the workflow does not revert the design
  (their sources live in this repo and produce the current style by default);
- the animated pieces (banner rain + snake) are the only motion on the page.

# Profile Maintenance Guide

How to keep this profile working and how to change it safely. Everything here
refers to files inside this repository (`SSSchangerSSS/SSSchangerSSS`).

## Repository map

| Path | What it is | Regenerated? |
|---|---|---|
| `README.md` / `README.fa.md` | Profile content (English / Persian) | manual |
| `assets/banner-light.svg`, `assets/banner-dark.svg` | Static identity banners | `make_banners.py` |
| `assets/github-stats-{light,dark}.svg` | Public stats card | `gen_stats_svg.py` (daily) |
| `assets/top-langs-{light,dark}.svg` | Language share card | `gen_stats_svg.py` (daily) |
| `.github/scripts/make_banners.py` | Banner source (single geometry → both themes) | — |
| `.github/scripts/gen_stats_svg.py` | Stats card generator | — |
| `.github/scripts/gen_snake_svg.py` | Contribution snake generator | — |
| `.github/scripts/test_generators.py` | Stdlib unit tests for both generators | — |
| `.github/workflows/stats.yml` | Daily stats regeneration (01:30 UTC) + push trigger | — |
| `.github/workflows/snake.yml` | Daily snake regeneration (00:00 UTC) + push trigger, publishes to the `output` branch | — |
| `output` branch | Hosts the two snake SVGs the README embeds | CI |

## Common changes

### Intro, projects, contact
Edit `README.md` and keep `README.fa.md` in sync (and vice versa). Both files
must list the same projects in the same order. Do not add contact channels you
have not verified; when you are ready to publish an email or LinkedIn, add a
line to the **Contact** section of both READMEs — nothing else needs to change.

### Banner text / colors
Edit `NAME` / `TAGLINE` / `THEMES` in `.github/scripts/make_banners.py`,
then run:

```bash
python .github/scripts/make_banners.py
```

This rewrites both `assets/banner-*.svg` from one geometry so the themes stay
consistent. Commit both files. The banners are intentionally static: keep them
free of SMIL/CSS animation, scripts and external references.

### Stats card colors & content
Colors live in `THEMES` in `.github/scripts/gen_stats_svg.py`. Rows live in
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
  (`lang_rows`), never by the displayed rows only;
- the commit row keeps its "public search index" label — it reflects
  `GET /search/commits?q=author:<user>`, not every commit ever made;
- missing values render as `—` with a "partial data" footer — never as
  fabricated zeros (`fmt_val`);
- if user+repos fetches both fail, the script exits non-zero and the previous
  SVGs stay untouched (do not remove that guard);
- keep writes atomic (`write_text_atomic`) so CI never publishes half a file.

### Snake
Tuning constants sit at the top of `.github/scripts/gen_snake_svg.py`:
`BASE_LEN`, `GROW`, `STEP_MS`, `BITE_EXTRA_MS`, `LEAD_MS`, `TAIL_HOLD_MS`,
`PAL` (palettes). The snake publishes to the `output` branch with the same
filenames, so README links stay valid. If GitHub's image cache ever serves a
stale snake, bump the `?v=` query on the two snake URLs in both READMEs.

### Schedules
Cron times live in the two workflow files. `snake.yml` runs at 00:00 UTC,
`stats.yml` at 01:30 UTC (deliberately staggered; both also run on pushes to
`main` and on manual dispatch). Both workflows are pinned to
`contents: write` only, run the generator tests first, and use
`concurrency` groups so overlapping runs cannot interleave commits.

## Running things locally

```bash
# tests (no network needed, uses synthetic data)
python .github/scripts/test_generators.py

# banners
python .github/scripts/make_banners.py

# stats cards (reads live GitHub data)
GH_STATS_TOKEN=<token> python .github/scripts/gen_stats_svg.py

# snake (reads live contribution calendar; writes dist/)
SNAKE_TOKEN=<token> python .github/scripts/gen_snake_svg.py
```

Any personal access token with public read access is enough for local runs;
CI uses the built-in `GITHUB_TOKEN`. Never commit a token or put one in a URL.

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

- every file referenced from the READMEs exists;
- all SVGs parse as XML (e.g. `python -c "from xml.dom import minidom; minidom.parse('<file>')"`);
- light **and** dark variants remain readable;
- the main content (name, intro, projects, links) is understandable with all
  images blocked;
- no fabricated numbers are published (stars, commits, skills, years...);
- rerunning both generators does not revert the design (their sources live in
  this repo and produce the current style by default).

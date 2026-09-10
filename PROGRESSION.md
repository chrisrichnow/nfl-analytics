# NFL Analytics — Progression Log

Manually maintained (this project is a subfolder of the EA monorepo, not its own git repo, so there's no per-project post-commit hook).

---

## 2026-09-09 — Project scaffolded and tool choice decided

Started as "second DE project, try Databricks/Spark." Rethought against the actual use case: NFL season stats are ~45-50K plays/season, fully structured, weekly batch updates — a warehouse-shaped problem, not a big-data one. Switched to Snowflake + dbt. Databricks/PySpark queued for a future project with real volume (NYC taxi data or NFL Next Gen Stats tracking data).

## 2026-09-09 — Environment setup

- Signed up for Snowflake free trial ($400 credit, 30 days), Standard edition, US East (Ohio).
- Created `nfl_wh` warehouse (XSMALL, auto-suspend 60s) and `nfl_analytics` database with `raw` / `staging` / `marts` schemas.
- System Python was 3.14 — too new, no working pandas/numpy wheels. Installed Python 3.12 via winget specifically for this project's venv.

## 2026-09-09 — Ingestion built and validated

- Original plan used `nfl_data_py`; dropped it — pinned to `pandas<2.0`, incompatible with any modern Python. Rewrote to pull the same underlying Parquet files directly from nflverse's GitHub releases with `requests` + `pandas.read_parquet`.
- 2026 season data not yet published by nflverse (season starts tonight) — validated the full pipeline against the completed 2025 season instead. Rerun with `NFL_SEASON=2026` once available.
- Dropped the pre-aggregated player-stats source (only covers through 2024) — player-game stats derived from play-by-play in dbt instead.
- Loaded: 48,771 PBP rows, 285 games, 36 team reference rows.

## 2026-09-09 — dbt models built

- 3 staging models (`stg_pbp`, `stg_schedules`, `stg_teams`) + 5 marts (`team_game_results`, `team_rankings`, `player_passing_leaders`, `player_rushing_leaders`, `player_receiving_leaders`).
- Hit two Snowflake-specific quirks: can't cast number directly to boolean (needs `::number::boolean`), and `ORDER BY DESC` sorts NULLs first by default (opposite of Postgres) — was putting null-stat rows at rank #1 until yardage columns were coalesced to 0.

## 2026-09-09 — dbt tests added, one real bug found

- Added 36 dbt tests (not-null, uniqueness, composite-key uniqueness via `dbt_utils`, referential integrity).
- Test failure surfaced a real data-quality issue: nflverse has inconsistent player-name abbreviations for the same `player_id` mid-season, splitting leaderboard rows. Fixed with `MODE()` instead of grouping on the raw name column.
- All 36 tests passing.

## 2026-09-09 — Schema names cleaned up

- dbt was prefixing custom schemas with the profile default (`staging_marts`, `staging_staging`). Added `generate_schema_name` macro override so models land in clean `staging` / `marts` schemas instead. Dropped orphaned old schemas.

## 2026-09-09 — Expanded player stats: defense, kicking, per-game splits

- Added `player_defense_leaders` (sacks with correct half-sack credit, interceptions - not a full box score, play-by-play has no tackle counts), `player_kicking_leaders` (FG/XP makes, attempts, %).
- Added per-game weekly splits for the three offensive categories (`player_passing_by_week`, `player_rushing_by_week`, `player_receiving_by_week`) alongside the existing season totals.
- Now 13 models, 49 dbt tests, all passing. Spot-checked: sack leaders, FG% leaders, and one player's weekly passing splits all look realistic.

## 2026-09-09 — Streamlit dashboard built

- Four-tab Streamlit app (`dashboard/`) reading the marts live from Snowflake: team rankings (diverging point-differential chart + standings), player leaders (all five stat categories), player explorer (week-by-week per player), and a pipeline explainer tab.
- Queries cached 10 min and the connection held open, so filter interaction doesn't repeatedly wake the credit-metered warehouse.
- Dependency snag: installing Streamlit downgraded protobuf below what dbt requires. Resolved by upgrading Streamlit to 1.63 and pinning `protobuf>=6,<7`; `pip check` is clean and both dbt and Streamlit work.
- Verified in a real browser via Playwright across all four tabs. Fixed three layout bugs found that way: team labels being thinned to every other row, long team names truncating, and rotated week-axis labels.

## 2026-09-09 — Published to GitHub

- Created standalone public repo `chrisrichnow/nfl-analytics` (separate from the EA monorepo, matching how golf-de-pipeline is published). Added `projects/nfl-analytics/` to the EA `.gitignore`.
- Scrubbed `.env.example`, which had the real Snowflake account identifier and username baked in, down to placeholders. Verified the password appears nowhere outside the ignored `.env`, and re-checked the published file list on GitHub after pushing.
- Added `docs/snowflake_setup.sql` so the warehouse/database/schema setup is reproducible from the repo rather than living only in Snowsight worksheet history.

## 2026-09-09 — Portfolio pass (matching golf-de-pipeline)

- Captured five dashboard screenshots to `docs/portfolio/` and embedded them in the README, including a hero image.
- Replaced the simple architecture flowchart with a full dbt lineage diagram (source → ingestion → raw → staging → marts → dashboard, with per-model nodes). Validated it actually renders by running Mermaid headlessly rather than assuming the syntax was right.
- Added `docs/portfolio/resume-entry.md` (resume bullets, portfolio card, interview intro, explicit claim boundaries) and `docs/portfolio/demo-walkthrough.md` (two-minute demo script plus likely follow-up questions).

## Next up

- Rerun ingestion + dbt with `NFL_SEASON=2026` once nflverse publishes the file.
- Fix cosmetic `dbt_utils.unique_combination_of_columns` deprecation warning (args should nest under `arguments:`).
- Optional stretch: orchestration (weekly scheduled rerun), dbt docs site, multi-season historical backfill.

## 2026-09-10 ? Gridiron dashboard (working changes)
- Added custom NFL dashboard with live cached Snowflake reads, overview/team/player/pipeline views, weekly profiles, CSV, and responsive styling.
- Verified against real warehouse data; browser checks passed for filters, export, player categories, weekly totals, error recovery, and mobile layout. Screenshots and launch guide included. Existing Streamlit app retained.

## 2026-09-10 ? NFL visual theme refresh
- At Chris's request, replaced golf-like greens with navy, red, white, a dark navigation rail, football icon, and scoreboard typography. Updated chart colors and conference legend. Browser checks passed.

## 2026-09-10 - Team identity tiles and NFL shield
- Added nflverse primary/secondary team colors to single-team spotlights and game-log headers, with contrast-aware text. Shared league panels retain the dashboard theme.
- Replaced the app icon with the NFL-hosted shield asset and documented asset sources. Browser checks passed; NFL image load and team detail styling verified.

## 2026-09-10 - Final NFL Analytics portfolio presentation
- Renamed the dashboard NFL Analytics; bundled NFL shield and team logos, and scoped team colors/logos to single-team panels.
- Refreshed eight screenshots for the final design and updated the README, demo walkthrough, and portfolio copy.
- Browser verification passed, including successful logo decoding for all 32 loaded teams, responsive views, exports, and error recovery.

## 2026-09-10 - Transparent player portraits
- Matched all 1,207 analytics players by GSIS ID against nflverse identity data and the 2026 roster reference.
- Bundled 1,206 verified transparent source headshots: 1,079 from the 2026 roster reference and 127 latest-available fallbacks. Sal Cannella had no working transparent image at the referenced NFL/ESPN URLs and displays an explicit unavailable state.
- Removed CSS backplates from all team logos and player portraits. Refreshed portfolio screenshots and passed browser, image-decoding, responsive-layout, export, and error-recovery checks.

## 2026-09-10 - Team logos and player comparison
- Replaced team abbreviation badges in overview and team-intelligence tables with transparent team logos.
- Added a dedicated Player Profiles view with lookup across modeled players, all available stat categories, and split-screen comparison for five selectable stat groups.
- Labeled career accolades unavailable because the warehouse and identity feed do not contain verified award histories. Added browser coverage and a portfolio comparison screenshot.

## 2026-09-10 - Seven-season historical backfill
- Refactored ingestion to accept validated season lists/ranges and load independent raw PBP tables without combining wide seasons in memory.
- Loaded and modeled the complete 2019–2025 seasons: 342,249 plays and 1,960 games. dbt unions schema-drifted raw tables by column name.
- All 13 models rebuilt and all 49 data tests passed. Dashboard/browser checks passed for seven selectable seasons; the transparent portrait manifest expanded to 2,899 of 2,900 modeled players.


## 2026-09-10 - Character rendering cleanup
- Replaced corrupted question-mark separators in player profile and comparison labels with clean pipe separators.
- Corrected player roster badges to display `LA | 2026 roster` and `NE | 2026 roster`, and refreshed the affected portfolio screenshots.
- Added browser assertions for malformed replacement characters and roster badge question marks; the complete dashboard check passes on desktop and mobile.

## Session Summary

**Date:** 2026-09-10
**Focus:** Turn the NFL data engineering project into a polished employer-facing analytics dashboard and expand its historical coverage.

### What Got Done
- Built and refined the custom NFL Analytics dashboard with season overview, team intelligence, five player leaderboards, player profiles, player comparisons, pipeline documentation, responsive layouts, and filtered CSV exports.
- Applied the NFL visual theme, NFL shield, all 32 transparent team logos, team-specific colors, and transparent player portraits. The portrait manifest covers 2,899 of 2,900 modeled players.
- Backfilled and modeled the 2019-2025 seasons in Snowflake: 342,249 plays and 1,960 games across all 32 teams.
- Rebuilt all 13 dbt models and passed all 49 data tests. The browser suite passes across all seven seasons, desktop and mobile views, filters, exports, image decoding, player comparison, and error recovery.
- Refreshed the repository portfolio screenshots and pushed all completed work through commit `c885aaf`.

### Decisions Made
- Use 2019 as the historical starting point, giving the dashboard seven complete seasons through 2025.
- Keep team colors and logos on panels dedicated to one team; retain the shared NFL theme for league-wide panels.
- Show accolade data as unavailable until a verified award source is added rather than inferring MVPs, Super Bowls, All-Pro selections, or Pro Bowls.
- Use the 2026 roster reference for current team labels and portraits while clearly labeling selected-season statistics separately.

### Open Items / Next Steps
- Load and model the 2026 season after nflverse publishes the source file.
- Add a verified accolades source if career awards are needed in player profiles.
- Sal Cannella remains the only modeled player without a verified transparent portrait.
- Optional engineering improvements: automate scheduled refreshes, publish dbt documentation, and fix the cosmetic `dbt_utils.unique_combination_of_columns` deprecation warning.

### Memory Updates
- Preferences learned: Chris prefers an NFL navy/red presentation, team branding only on team-specific panels, transparent logos and portraits, and clean employer-facing visuals without malformed glyphs.
- Decisions to log: historical dashboard coverage begins with 2019; unverified accolades remain explicitly unavailable.

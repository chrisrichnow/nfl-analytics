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

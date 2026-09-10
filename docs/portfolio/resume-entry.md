# Resume and portfolio copy

## Resume entry

**NFL Analytics Warehouse** | Snowflake, dbt, SQL, Python, JavaScript

- Built a multi-season ELT pipeline loading 342,249 play-by-play rows across 1,960 games (2019–2025) into Snowflake, then modeled them with dbt into 13 layered models covering team rankings and player stats at season and weekly grain.
- Derived player statistics from raw play-by-play rather than pre-aggregated tables, correctly attributing passing, rushing, receiving, kicking, and defensive plays—including the NFL's half-sack convention—across 2,900 unique players.
- Wrote 49 dbt tests covering not-null and uniqueness constraints, composite-key uniqueness, and referential integrity; those tests caught a source data-quality defect where inconsistent player-name spellings were splitting leaderboard rows, resolved by keying on player ID and resolving names with `MODE()`.
- Built an interactive NFL Analytics dashboard over Snowflake marts, with team and player drilldowns, filtered CSV exports, responsive layouts, and ten-minute query caching.

## Short version

Built a Snowflake + dbt warehouse turning 342,249 NFL play-by-play rows from 2019–2025 into tested team and player analytics, with 49 dbt tests and an interactive comparison dashboard.

## Portfolio card

**Title:** NFL Analytics Warehouse

**Description:** A Snowflake and dbt pipeline that turns seven complete seasons of raw NFL play-by-play into team rankings and player leaderboards across offense, defense, and kicking. Includes layered staging and mart models, 49 data-quality tests, and an interactive comparison dashboard.

**Tags:** Snowflake · dbt · SQL · Python · JavaScript · Data quality · Dimensional modeling

## Interview introduction (about 30 seconds)

"I built an NFL analytics warehouse to practice dimensional modeling with dbt. It pulls play-by-play data into Snowflake raw tables, then dbt builds staging views and mart tables for team rankings and player leaderboards. The interesting part was that the source is one wide table with 370 columns and no leaderboards in it — every stat has to be attributed to the right player from role-specific columns, and sacks need the NFL's half-credit rule for shared sacks. My tests also caught a real source defect where the same player ID had two different name spellings mid-season, which was splitting his stats into two leaderboard rows."

## The tool-choice story (worth telling)

This project started as a Databricks and PySpark build. Reassessing it against the actual data changed the decision: an NFL season is roughly 48,000 plays — hundreds of thousands of rows, fully structured, updated in weekly batches. That is warehouse-shaped, not big-data-shaped, and a Spark cluster would have added cost and operational overhead without buying anything. Snowflake and dbt was the right-sized choice, and being able to explain *why* a tool was not used is often more convincing than listing it.

## Claim boundaries

- Counts describe the verified September 10, 2026 dataset covering the completed 2019–2025 seasons. This is a personal learning project, not a production deployment.
- The 2026 season is not part of the validated historical range. Describe the warehouse as covering 2019–2025 unless 2026 has actually been loaded and tested.
- Defensive statistics cover sacks and interceptions only. Play-by-play does not carry tackle counts, so this is not a complete defensive box score — say so rather than implying full defensive coverage.
- No orchestration is implemented. Reruns are manual; there is no Airflow or dbt Cloud scheduling.
- Implementation used AI assistance. Be able to explain the architecture, the modeling decisions, and the tradeoffs in your own words; do not describe the work as independently hand-coded.
- This is a separate project from the PGA prediction models and the golf data pipeline. Do not combine their scope or metrics.

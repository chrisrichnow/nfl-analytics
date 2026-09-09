# Two-minute project demo

## Before presenting

The dashboard reads Snowflake live, so the warehouse needs to be resumable and `.env` needs valid credentials. No ingestion run is required — the marts are already built.

**PowerShell, from the project root:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Open http://localhost:8501. The first query takes a few seconds while `nfl_wh` resumes from auto-suspend; after that it is cached for 10 minutes.

## Walkthrough

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Header metrics and the point-differential chart | "This is an NFL analytics warehouse built on Snowflake and dbt. It's reading about 49,000 plays from a full season, modeled into team rankings and player leaderboards. Blue teams outscored their opponents, red got outscored." |
| 0:20–0:40 | Player leaders tab, Passing selected | "Every player stat here is derived from raw play-by-play, not loaded from a pre-aggregated stats file. The source publishes one row per play with about 370 columns, so passing yards means attributing each play to the right passer and summing it." |
| 0:40–1:00 | Switch category to Defense; point at the `.5` values | "Defense is the same idea but harder. Sacks are split across three different columns in the source, and the NFL credits half a sack to each player on a shared one — so the model unions those columns with the right credit weights." |
| 1:00–1:20 | Player explorer; pick a quarterback; point at the bye-week gap | "Season totals and weekly splits come from the same staging view at different grains, so they can never disagree. The gap here is his bye week — there's no row, rather than a zero, which is the honest representation." |
| 1:20–1:45 | `dbt_project/models/marts/player_defense_leaders.sql` and `_marts.yml` | "Forty-nine dbt tests run against these models — uniqueness on composite keys like season plus player, and referential integrity between schedules and the team reference table. The tests caught a real bug: the source spelled one player's name two ways mid-season, which split his stats into two leaderboard rows." |
| 1:45–2:00 | README architecture diagram | "Python lands raw Parquet in Snowflake untouched, dbt builds staging views and mart tables on top, and the dashboard only ever reads the marts. The raw layer is never transformed, so I can always rebuild everything downstream from the original source." |

## Likely follow-up questions

**Why Snowflake and dbt instead of Databricks or Spark?** A season is roughly 48,000 plays — hundreds of thousands of rows, fully structured, batch-updated weekly. That does not need distributed compute. A Spark cluster would have added cost and setup overhead without buying anything at that volume. Spark earns its place when data volume or shape actually forces it.

**Why derive player stats instead of loading them?** Two reasons. The practical one: nflverse's pre-aggregated player-stats file only covers seasons through 2024, so it is unusable for a current season. The better one: deriving from raw play-by-play means the aggregation logic is mine and testable, rather than depending on someone else's black box.

**What did the tests actually catch?** A composite-uniqueness test on `season + player_id` failed on the receiving leaderboard. The cause was source-side: nflverse disambiguates player names when two players share a surname, so the same player ID appeared as both `M.Wilson` and `Mi.Wilson` mid-season, splitting his stats across two rows. Fixed by grouping on the ID alone and resolving the display name with `MODE()`.

**What's missing?** Tackle counts — play-by-play does not carry them, so defense covers sacks and interceptions only. There is also no orchestration yet; reruns are manual. Adding a weekly scheduled run is the natural next step now that the season is live.

**How do you control cost?** The warehouse is XSMALL with a 60-second auto-suspend, so it is not billing while idle. The dashboard caches query results for 10 minutes and holds one connection open, so clicking through filters does not repeatedly wake the warehouse.

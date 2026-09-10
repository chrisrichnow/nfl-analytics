# Two-minute project demo

Run `.\.venv\Scripts\python.exe dashboard-web/server.py` from the project root and open http://localhost:8054. Existing Snowflake configuration and network access are required. The initial query may resume the warehouse; results are cached for ten minutes. No ingestion is needed if the marts are already loaded.

| Time | Show | Explain |
|---|---|---|
| 0:00-0:20 | Season overview | 342,249 plays and 1,960 games across seven complete seasons, 2019–2025. The season selector changes every team and player view. |
| 0:20-0:40 | Select the spotlight team | Team game logs and scoring balance. Rankings order total wins, then differential; displayed records account for ties. |
| 0:40-1:00 | Player leaders: Passing, then Defense | Player stats are derived from raw play-by-play. Shared sacks receive half credit; defense excludes tackle counts. |
| 1:00-1:20 | Select a passer | Weekly bars show recorded performance. Missing weeks are gaps, not zeros. Weekly yardage reconciles with the season total. |
| 1:20-1:45 | Behind the data | Python loads one raw table per season, dbt unions schema changes by column name, and 49 tests validate the resulting models. |
| 1:45-2:00 | Search a leaderboard and export CSV | Filters operate on cached data; exports include all matching rows. Explain the practical value of making warehouse outputs easy to explore. |

## Useful follow-ups

- **Why Snowflake/dbt?** The loaded season is structured and small enough for warehouse SQL; distributed Spark processing was unnecessary for this scope.
- **A real quality issue:** Different abbreviations for one player split leaderboard rows. Grouping by player ID and choosing the modal display name resolved it.
- **Cost:** SELECT-only queries are cached for ten minutes; the configured warehouse auto-suspends when idle. Refresh does not ingest new games.
- **Limits:** Local portfolio application, manual pipeline runs, no betting integration, no tackles, and no minimum attempts for rate rankings. Separate queries are not an atomic snapshot during a concurrent dbt rebuild.

Current screenshots are in `docs/portfolio/gridiron/`; older Streamlit screenshots are historical.

# NFL Analytics dashboard

A custom portfolio interface over the existing Snowflake/dbt project. Football broadcast styling with navy, red, and white, responsive layouts, and charts drawn locally without CDN dependencies. The original Streamlit dashboard remains available in `../dashboard/`.

From the NFL project root:

```powershell
.\.venv\Scripts\python.exe dashboard-web/server.py
```

Open **http://localhost:8054**. The existing `.env` supplies Snowflake credentials; the browser never receives them. Requires warehouse network access and the existing Python dependencies. The server binds to localhost and is intended for local use.

## Views

- **Season overview:** season spotlight, coverage metrics, point-differential leaders, scoring scatterplot, and sortable standings.
- **Team intelligence:** conference/search filters, W–L–T records, scoring comparisons, and team game logs.
- **Player leaders:** searchable, sortable passing/rushing/receiving/defense/kicking boards; metric selection; player profiles and offensive weekly charts.
- **Behind the data:** model inventory, row counts, pipeline explanation, and saved dbt validation status.

CSV exports include every matching leaderboard/standings row, across pagination. The data page exports the mart inventory. Weekly detail rows are visible in the player profile. Missing weeks are gaps, not fabricated zeros.

## Data semantics

All loaded seasons are selectable. Season totals include postseason. Rankings preserve the mart's ordering by total wins, then differential, and are not predictive ratings. The UI calculates team losses/ties from game results, with half-win credit for ties in win percentage, because the current ranking mart treats all non-wins as losses.

Player rates have no minimum sample threshold. Defense contains sacks/interceptions, not tackles. Source player abbreviations are retained. EPA is a play-level measure on the plays included by each mart. The local dbt artifact reports its own timestamp; the dashboard does not run dbt tests or claim current validation when the artifact is absent.

The server issues SELECT queries against ten marts plus staging coverage and game-type summaries. An in-memory ten-minute cache prevents filter clicks and repeated refreshes from triggering new warehouse queries. After expiry, the next request queries Snowflake. Refresh does not ingest source data. Separate SELECT statements are not an atomic snapshot across a concurrent dbt rebuild; avoid refreshing during model rebuilds for a consistent demo.

## Verification

With Node.js, Playwright, Microsoft Edge, and the dashboard running:

```powershell
# If Playwright is not already installed in a parent workspace:
npm.cmd install --no-save playwright@1.58.2
node dashboard-web/check.cjs
```

Override `NFL_DASHBOARD_URL` to test a different port. The browser check uses actual warehouse responses and covers filtering, CSV content, all player categories, weekly/season reconciliation for the leading passer, error recovery, and mobile width. Screenshots are written to `docs/portfolio/gridiron/`.

Verified September 10, 2026: 48,771 play-by-play rows, 285 games, 32 teams; saved September 9 dbt artifact reports 49/49 passing. These are observed project data, not an independently certified NFL feed.


## Team identity and logo assets

Single-team spotlight and game-log headers use primary/secondary colors from the [nflverse team reference](https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/teams_colors_logos.csv), saved in `team-colors-source.csv`. Text switches between white and dark ink for contrast. League comparison panels keep the navy/red dashboard theme. Player marts do not contain reliable team attribution, so player panels remain neutral.

The NFL shield is sourced from [NFL Football Operations](https://operations.nfl.com/) ([original PNG](https://static.www.nfl.com/image/upload/v1554321393/league/nvfr7ogywskqrfaiu38m.png)); `favicon.svg` embeds that unmodified PNG for the existing local asset route. Retrieved September 10, 2026.

Team logo PNGs are bundled as data URLs in `app.js` using the ESPN URLs in the saved nflverse reference. Single-team spotlight and game-log panels show the matching logo; league comparisons remain neutral.

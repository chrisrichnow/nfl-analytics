"""
Pull current-season NFL play-by-play, weekly player stats, schedules, and team
reference data directly from nflverse's public GitHub release Parquet files,
and load them as-is into Snowflake raw tables.

No cleaning/transformation here on purpose - this is the bronze/raw layer.
dbt staging models handle typing, dedup, and conforming downstream.

Source: https://github.com/nflverse/nflverse-data/releases
"""

import io
import os

import pandas as pd
import requests
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

SEASON = int(os.getenv("NFL_SEASON", 2026))

RELEASE_BASE = "https://github.com/nflverse/nflverse-data/releases/download"

SOURCES = {
    f"PBP_{SEASON}": f"{RELEASE_BASE}/pbp/play_by_play_{SEASON}.parquet",
    "SCHEDULES": f"{RELEASE_BASE}/schedules/games.parquet",
    "TEAMS": f"{RELEASE_BASE}/teams/teams_colors_logos.parquet",
}
# Player-game stats are derived downstream in dbt from play-by-play rather than
# loaded pre-aggregated - nflverse's combined player_stats.parquet file only
# covers seasons through 2024, so it can't be used for the current season anyway.

CONN_PARAMS = {
    "account": os.environ["SNOWFLAKE_ACCOUNT"],
    "user": os.environ["SNOWFLAKE_USER"],
    "password": os.environ["SNOWFLAKE_PASSWORD"],
    "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
    "database": os.environ["SNOWFLAKE_DATABASE"],
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "raw"),
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
}


def fetch_parquet(url: str) -> pd.DataFrame | None:
    resp = requests.get(url, timeout=120)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return pd.read_parquet(io.BytesIO(resp.content))


def load_table(conn, df: pd.DataFrame, table_name: str) -> None:
    if df.empty:
        print(f"  {table_name}: no rows returned, skipping")
        return
    # Snowflake wants uppercase, unquoted column names by convention
    df.columns = [c.upper() for c in df.columns]
    success, _, nrows, _ = write_pandas(
        conn, df, table_name, auto_create_table=True, overwrite=True
    )
    print(f"  {table_name}: loaded {nrows} rows (success={success})")


def main() -> None:
    print(f"Pulling {SEASON} season data from nflverse GitHub releases...")

    with snowflake.connector.connect(**CONN_PARAMS) as conn:
        for table_name, url in SOURCES.items():
            print(f"Fetching {table_name} from {url} ...")
            df = fetch_parquet(url)
            if df is None:
                print(
                    f"  {table_name}: source file not published yet (404), "
                    "skipping - nflverse usually posts it after week 1 games. Rerun later."
                )
                continue
            # weekly stats and schedules span all seasons; filter to the target one
            if "season" in df.columns and table_name != "TEAMS":
                df = df[df["season"] == SEASON]
            load_table(conn, df, table_name)

    print("Done.")


if __name__ == "__main__":
    main()

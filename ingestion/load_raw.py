"""Load one or more nflverse seasons into Snowflake raw tables.

Examples:
    python ingestion/load_raw.py --seasons 2019-2025
    python ingestion/load_raw.py --seasons 2019,2020,2021

Each play-by-play season is replaced independently as RAW.PBP_<YEAR>. Schedules
are replaced once with only the requested seasons; team reference data is also
replaced. Transformations remain downstream in dbt.
"""
import argparse
import io
import os
from datetime import date

import pandas as pd
import requests
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

RELEASE_BASE = "https://github.com/nflverse/nflverse-data/releases/download"
MIN_SEASON = 1999

def connection_params() -> dict[str, str]:
    """Read credentials only when a real load starts, keeping parser tests offline."""
    return {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "raw"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    }


def parse_seasons(value: str) -> list[int]:
    """Parse comma-separated years and inclusive ranges into sorted years."""
    years = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"Invalid descending range: {part}")
            years.update(range(start, end + 1))
        else:
            years.add(int(part))
    latest = date.today().year
    if not years or min(years) < MIN_SEASON or max(years) > latest:
        raise ValueError(f"Seasons must be between {MIN_SEASON} and {latest}")
    return sorted(years)


def fetch_parquet(url: str) -> pd.DataFrame | None:
    response = requests.get(url, timeout=180)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))


def load_table(conn, df: pd.DataFrame, table_name: str) -> int:
    if df.empty:
        print(f"  {table_name}: no rows returned, skipping", flush=True)
        return 0
    df.columns = [column.upper() for column in df.columns]
    success, _, rows, _ = write_pandas(
        conn, df, table_name, auto_create_table=True, overwrite=True
    )
    if not success or rows != len(df):
        raise RuntimeError(
            f"{table_name}: expected {len(df)} rows but Snowflake reported {rows}"
        )
    print(f"  {table_name}: loaded {rows:,} rows", flush=True)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default = os.getenv("NFL_SEASONS", os.getenv("NFL_SEASON", "2019-2025"))
    parser.add_argument("--seasons", default=default, help="Example: 2019-2025 or 2024,2025")
    args = parser.parse_args()
    try:
        seasons = parse_seasons(args.seasons)
    except ValueError as error:
        parser.error(str(error))

    print(f"Loading nflverse seasons {seasons[0]}-{seasons[-1]} into Snowflake...", flush=True)
    with snowflake.connector.connect(**connection_params()) as conn:
        for season in seasons:
            table = f"PBP_{season}"
            url = f"{RELEASE_BASE}/pbp/play_by_play_{season}.parquet"
            print(f"Fetching {table}...", flush=True)
            frame = fetch_parquet(url)
            if frame is None:
                print(f"  {table}: source is not published; leaving any existing table unchanged", flush=True)
                continue
            if "season" in frame.columns:
                frame = frame[frame["season"] == season]
            load_table(conn, frame, table)
            del frame

        print("Fetching schedules...", flush=True)
        schedules = fetch_parquet(f"{RELEASE_BASE}/schedules/games.parquet")
        if schedules is None:
            raise RuntimeError("The combined schedule source was not available")
        schedules = schedules[schedules["season"].isin(seasons)]
        load_table(conn, schedules, "SCHEDULES")

        print("Fetching team reference...", flush=True)
        teams = fetch_parquet(f"{RELEASE_BASE}/teams/teams_colors_logos.parquet")
        if teams is None:
            raise RuntimeError("The team-reference source was not available")
        load_table(conn, teams, "TEAMS")

    print("Raw multi-season load complete. Run dbt models and tests next.", flush=True)


if __name__ == "__main__":
    main()

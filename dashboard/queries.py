"""Read-only Snowflake access for the dashboard.

Every query is cached so interacting with the UI does not re-hit the warehouse -
the trial account is credit-metered and the warehouse auto-suspends after 60s.
"""

import os

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CACHE_TTL = 600  # seconds


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="marts",
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        client_session_keep_alive=True,
    )


@st.cache_data(ttl=CACHE_TTL)
def run_query(sql: str) -> pd.DataFrame:
    cur = get_connection().cursor()
    try:
        cur.execute(sql)
        df = cur.fetch_pandas_all()
    finally:
        cur.close()
    df.columns = [c.lower() for c in df.columns]
    return df


# Leaderboard config: which mart, which metric to chart, which columns to show.
LEADERBOARD_SPECS = {
    "Passing": {
        "table": "player_passing_leaders",
        "weekly_table": "player_passing_by_week",
        "metric": "passing_yards",
        "metric_label": "Passing yards",
        "columns": [
            "player_name", "attempts", "completions", "passing_yards",
            "passing_touchdowns", "interceptions", "avg_epa",
        ],
    },
    "Rushing": {
        "table": "player_rushing_leaders",
        "weekly_table": "player_rushing_by_week",
        "metric": "rushing_yards",
        "metric_label": "Rushing yards",
        "columns": [
            "player_name", "carries", "rushing_yards", "rushing_touchdowns",
            "yards_per_carry", "avg_epa",
        ],
    },
    "Receiving": {
        "table": "player_receiving_leaders",
        "weekly_table": "player_receiving_by_week",
        "metric": "receiving_yards",
        "metric_label": "Receiving yards",
        "columns": [
            "player_name", "targets", "receptions", "receiving_yards",
            "receiving_touchdowns", "avg_epa",
        ],
    },
    "Defense": {
        "table": "player_defense_leaders",
        "weekly_table": None,
        "metric": "sacks",
        "metric_label": "Sacks",
        "columns": ["player_name", "sacks", "interceptions"],
    },
    "Kicking": {
        "table": "player_kicking_leaders",
        "weekly_table": None,
        "metric": "fg_made",
        "metric_label": "Field goals made",
        "columns": [
            "player_name", "fg_made", "fg_attempts", "fg_pct",
            "xp_made", "xp_attempts", "xp_pct", "avg_made_fg_distance",
        ],
    },
}


@st.cache_data(ttl=CACHE_TTL)
def available_seasons() -> list[int]:
    df = run_query("select distinct season from marts.team_rankings order by season desc")
    return df["season"].astype(int).tolist()


def team_rankings(season: int) -> pd.DataFrame:
    return run_query(
        f"select * from marts.team_rankings where season = {season} order by power_rank"
    )


def leaderboard(category: str, season: int) -> pd.DataFrame:
    spec = LEADERBOARD_SPECS[category]
    return run_query(
        f"select * from marts.{spec['table']} where season = {season}"
    )


def weekly_for_player(category: str, season: int, player_id: str) -> pd.DataFrame:
    spec = LEADERBOARD_SPECS[category]
    if not spec["weekly_table"]:
        return pd.DataFrame()
    # player_id comes from a selectbox populated by this same database, not user
    # free-text, but parameterize anyway rather than interpolating a string.
    cur = get_connection().cursor()
    try:
        cur.execute(
            f"select * from marts.{spec['weekly_table']} "
            "where season = %s and player_id = %s order by week",
            (season, player_id),
        )
        df = cur.fetch_pandas_all()
    finally:
        cur.close()
    df.columns = [c.lower() for c in df.columns]
    return df


@st.cache_data(ttl=CACHE_TTL)
def pipeline_stats(season: int) -> dict:
    counts = run_query(
        f"""
        select
            (select count(*) from raw.pbp_{season}) as plays,
            (select count(*) from marts.team_game_results where season = {season}) / 2 as games,
            (select count(*) from marts.team_rankings where season = {season}) as teams,
            (select count(distinct player_id) from marts.player_receiving_leaders where season = {season})
                as receivers,
            (select count(distinct player_id) from marts.player_passing_leaders where season = {season})
                as passers,
            (select count(distinct player_id) from marts.player_defense_leaders where season = {season})
                as defenders
        """
    )
    return counts.iloc[0].to_dict()

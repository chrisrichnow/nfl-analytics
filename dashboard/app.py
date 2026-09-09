"""NFL Analytics dashboard - reads the dbt marts live from Snowflake.

Run from the project root:
    .venv\\Scripts\\python.exe -m streamlit run dashboard/app.py
"""

import altair as alt
import pandas as pd
import streamlit as st

import queries as q

# Palette roles (light surface). Series 1 blue for single-series magnitude;
# blue/red as the diverging pair for point differential polarity.
BLUE = "#2a78d6"
RED = "#e34948"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
MUTED = "#898781"
SURFACE = "#fcfcfb"

st.set_page_config(page_title="NFL Analytics", page_icon="🏈", layout="wide")


PRETTY_OVERRIDES = {
    "avg_epa": "Avg EPA",
    "fg_pct": "FG %",
    "xp_pct": "XP %",
    "fg_made": "FG made",
    "fg_attempts": "FG att",
    "xp_made": "XP made",
    "xp_attempts": "XP att",
    "avg_made_fg_distance": "Avg made FG dist",
    "yards_per_carry": "Yards/carry",
}


def prettify(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(
        columns={
            c: PRETTY_OVERRIDES.get(c, c.replace("_", " ").capitalize())
            for c in df.columns
        }
    )


def style(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0, fill=SURFACE)
        .configure_axis(
            gridColor=GRID,
            gridWidth=1,
            domainColor=AXIS,
            tickColor=AXIS,
            labelColor=MUTED,
            titleColor=MUTED,
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_legend(labelColor=MUTED, titleColor=MUTED)
    )


st.title("NFL Analytics")
st.caption(
    "Team power rankings and player stats, derived from nflverse play-by-play "
    "through a Snowflake + dbt pipeline."
)

seasons = q.available_seasons()
season = st.sidebar.selectbox("Season", seasons, index=0)
st.sidebar.caption(
    "Data is queried live from Snowflake (`nfl_analytics` database, `marts` schema). "
    "Results are cached for 10 minutes to limit warehouse credit use."
)

stats = q.pipeline_stats(season)
cols = st.columns(5)
cols[0].metric("Plays", f"{int(stats['plays']):,}")
cols[1].metric("Games", f"{int(stats['games']):,}")
cols[2].metric("Teams", int(stats["teams"]))
cols[3].metric("Passers", int(stats["passers"]))
cols[4].metric("Receivers", int(stats["receivers"]))

tab_teams, tab_leaders, tab_player, tab_pipeline = st.tabs(
    ["Team rankings", "Player leaders", "Player explorer", "Pipeline"]
)


# ---------------------------------------------------------------- team rankings
with tab_teams:
    teams = q.team_rankings(season)

    conf = st.radio(
        "Conference", ["All", "AFC", "NFC"], horizontal=True, key="conf_filter"
    )
    view = teams if conf == "All" else teams[teams["team_conf"] == conf]

    st.subheader("Point differential")
    st.caption("Points scored minus points allowed. Blue = outscored opponents, red = outscored by them.")

    diff_base = alt.Chart(view).encode(
        y=alt.Y(
            "team_name:N",
            sort="-x",
            title=None,
            axis=alt.Axis(labelLimit=200, labelOverlap=False),
        )
    )
    diff_bars = diff_base.mark_bar(cornerRadiusEnd=4, height=14).encode(
        x=alt.X("point_diff:Q", title="Point differential"),
        color=alt.condition(
            alt.datum.point_diff >= 0, alt.value(BLUE), alt.value(RED)
        ),
        tooltip=[
            alt.Tooltip("team_name:N", title="Team"),
            alt.Tooltip("wins:Q", title="Wins"),
            alt.Tooltip("losses:Q", title="Losses"),
            alt.Tooltip("win_pct:Q", title="Win %", format=".3f"),
            alt.Tooltip("points_for:Q", title="Points for"),
            alt.Tooltip("points_against:Q", title="Points against"),
            alt.Tooltip("point_diff:Q", title="Differential"),
        ],
    )
    zero_rule = alt.Chart(view).mark_rule(color=AXIS, strokeWidth=1).encode(x=alt.datum(0))
    diff_chart = (diff_bars + zero_rule).properties(height=max(320, 28 * len(view)))
    st.altair_chart(style(diff_chart), use_container_width=True)

    st.subheader("Standings")
    st.dataframe(
        view[[
            "power_rank", "team_name", "team_conf", "team_division", "games_played",
            "wins", "losses", "win_pct", "points_for", "points_against",
            "point_diff", "avg_point_diff",
        ]].rename(columns={
            "power_rank": "Rank", "team_name": "Team", "team_conf": "Conf",
            "team_division": "Division", "games_played": "GP", "wins": "W",
            "losses": "L", "win_pct": "Win %", "points_for": "PF",
            "points_against": "PA", "point_diff": "Diff", "avg_point_diff": "Avg diff",
        }),
        hide_index=True,
        use_container_width=True,
    )


# --------------------------------------------------------------- player leaders
with tab_leaders:
    category = st.selectbox(
        "Category", list(q.LEADERBOARD_SPECS.keys()), key="leader_category"
    )
    spec = q.LEADERBOARD_SPECS[category]
    board = q.leaderboard(category, season)

    top_n = st.slider("Show top", 5, 40, 15, key="leader_top_n")
    ranked = board.nlargest(top_n, spec["metric"])

    st.subheader(f"{spec['metric_label']} leaders")

    bars = (
        alt.Chart(ranked)
        .mark_bar(cornerRadiusEnd=4, height=14, color=BLUE)
        .encode(
            x=alt.X(f"{spec['metric']}:Q", title=spec["metric_label"]),
            y=alt.Y(
                "player_name:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=200, labelOverlap=False),
            ),
            tooltip=[
                alt.Tooltip(c, title=c.replace("_", " ").title())
                for c in spec["columns"]
            ],
        )
    )
    labels = bars.mark_text(align="left", dx=4, color=MUTED, fontSize=11).encode(
        text=alt.Text(f"{spec['metric']}:Q", format=",")
    )
    st.altair_chart(
        style((bars + labels).properties(height=max(280, 28 * len(ranked)))),
        use_container_width=True,
    )

    st.subheader("Full leaderboard")
    st.dataframe(
        prettify(board[spec["columns"]].sort_values(spec["metric"], ascending=False)),
        hide_index=True,
        use_container_width=True,
    )


# -------------------------------------------------------------- player explorer
with tab_player:
    weekly_categories = [
        c for c, s in q.LEADERBOARD_SPECS.items() if s["weekly_table"]
    ]
    category = st.selectbox("Category", weekly_categories, key="explorer_category")
    spec = q.LEADERBOARD_SPECS[category]
    board = q.leaderboard(category, season).sort_values(
        spec["metric"], ascending=False
    )

    if board.empty:
        st.info("No player data for this season yet.")
    else:
        labels_to_id = dict(zip(board["player_name"], board["player_id"]))
        player_name = st.selectbox(
            "Player", list(labels_to_id.keys()), key="explorer_player"
        )
        weekly = q.weekly_for_player(category, season, labels_to_id[player_name])

        if weekly.empty:
            st.info("No week-by-week rows for this player.")
        else:
            st.subheader(f"{player_name} - {spec['metric_label'].lower()} by week")

            line = (
                alt.Chart(weekly)
                .mark_line(
                    strokeWidth=2,
                    color=BLUE,
                    point=alt.OverlayMarkDef(size=70, fill=BLUE, stroke=SURFACE, strokeWidth=2),
                )
                .encode(
                    x=alt.X("week:O", title="Week", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y(f"{spec['metric']}:Q", title=spec["metric_label"]),
                    tooltip=[
                        alt.Tooltip("week:O", title="Week"),
                        *[
                            alt.Tooltip(c, title=c.replace("_", " ").title())
                            for c in weekly.columns
                            if c not in ("season", "week", "player_id", "player_name")
                        ],
                    ],
                )
                .properties(height=340)
            )
            st.altair_chart(style(line), use_container_width=True)

            st.dataframe(
                prettify(weekly.drop(columns=["season", "player_id", "player_name"])),
                hide_index=True,
                use_container_width=True,
            )


# -------------------------------------------------------------------- pipeline
with tab_pipeline:
    st.subheader("How this data gets here")
    st.markdown(
        """
**Source:** nflverse publishes NFL play-by-play, schedules, and team reference data
as public Parquet files on GitHub.

**Load** (`ingestion/load_raw.py`): pulls those files and lands them untouched in the
Snowflake `raw` schema. No transformation at this stage, so the source is always
recoverable.

**Staging** (dbt views in `staging`): types and cleans the data. `stg_pbp` picks the
~40 relevant columns out of nflverse's ~370-column play-by-play schema.

**Marts** (dbt tables in `marts`): the tables this dashboard reads. Team rankings are
built from schedules; every player stat is derived from play-by-play rather than
loaded pre-aggregated.

**Tests:** 49 dbt tests run against the models - not-null and uniqueness on keys,
composite-key uniqueness (`season + team`, `season + week + player_id`), and
referential integrity between schedules and the team reference table.
        """
    )

    st.subheader("Coverage this season")
    st.dataframe(
        pd.DataFrame(
            [
                {"Metric": "Raw plays loaded", "Value": f"{int(stats['plays']):,}"},
                {"Metric": "Games", "Value": f"{int(stats['games']):,}"},
                {"Metric": "Teams", "Value": int(stats["teams"])},
                {"Metric": "Players with pass attempts", "Value": int(stats["passers"])},
                {"Metric": "Players with targets", "Value": int(stats["receivers"])},
                {"Metric": "Players with a sack or interception", "Value": int(stats["defenders"])},
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Known gap: defensive stats cover sacks and interceptions only. "
        "Play-by-play does not carry tackle counts, so this is not a full defensive box score."
    )

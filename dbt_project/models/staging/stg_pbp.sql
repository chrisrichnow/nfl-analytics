-- Union raw seasons by column name before selecting the stable analytics subset.
-- dbt_utils fills schema-drift columns with null instead of relying on column order.
with raw_pbp as (
    {{ dbt_utils.union_relations(
        relations=[
            source('raw', 'pbp_2019'),
            source('raw', 'pbp_2020'),
            source('raw', 'pbp_2021'),
            source('raw', 'pbp_2022'),
            source('raw', 'pbp_2023'),
            source('raw', 'pbp_2024'),
            source('raw', 'pbp_2025')
        ],
        source_column_name=None
    ) }}
)

select
    play_id::number as play_id,
    game_id,
    season::number as season,
    week::number as week,
    season_type,
    game_date::date as game_date,
    home_team,
    away_team,
    posteam,
    defteam,
    qtr::number as qtr,
    down::number as down,

    -- play classification
    coalesce(pass_attempt, 0)::number::boolean as is_pass_attempt,
    coalesce(rush_attempt, 0)::number::boolean as is_rush_attempt,
    coalesce(complete_pass, 0)::number::boolean as is_complete_pass,
    coalesce(touchdown, 0)::number::boolean as is_touchdown,
    coalesce(pass_touchdown, 0)::number::boolean as is_pass_touchdown,
    coalesce(rush_touchdown, 0)::number::boolean as is_rush_touchdown,
    coalesce(interception, 0)::number::boolean as is_interception,
    coalesce(sack, 0)::number::boolean as is_sack,
    coalesce(fumble_lost, 0)::number::boolean as is_fumble_lost,

    -- player attribution
    passer_player_id,
    passer_player_name,
    coalesce(passing_yards, 0)::number as passing_yards,
    rusher_player_id,
    rusher_player_name,
    coalesce(rushing_yards, 0)::number as rushing_yards,
    receiver_player_id,
    receiver_player_name,
    coalesce(receiving_yards, 0)::number as receiving_yards,

    -- defense: sacks (full + half-credit) and interceptions
    sack_player_id,
    sack_player_name,
    half_sack_1_player_id,
    half_sack_1_player_name,
    half_sack_2_player_id,
    half_sack_2_player_name,
    interception_player_id,
    interception_player_name,

    -- kicking
    coalesce(field_goal_attempt, 0)::number::boolean as is_field_goal_attempt,
    field_goal_result,
    kick_distance::number as kick_distance,
    coalesce(extra_point_attempt, 0)::number::boolean as is_extra_point_attempt,
    extra_point_result,
    kicker_player_id,
    kicker_player_name,

    -- scoring context
    posteam_score::number as posteam_score,
    defteam_score::number as defteam_score,
    epa::float as epa,
    wpa::float as wpa

from raw_pbp
where game_id is not null

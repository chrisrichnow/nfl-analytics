-- Unpivots schedules into one row per team per game (home + away), so team
-- rankings can be a simple group-by instead of a home/away case-when mess.
with home as (
    select
        season, week, game_id, game_date,
        home_team as team,
        away_team as opponent,
        home_score as points_for,
        away_score as points_against,
        is_division_game
    from {{ ref('stg_schedules') }}
),

away as (
    select
        season, week, game_id, game_date,
        away_team as team,
        home_team as opponent,
        away_score as points_for,
        home_score as points_against,
        is_division_game
    from {{ ref('stg_schedules') }}
)

select
    *,
    points_for > points_against as is_win,
    points_for - points_against as point_diff
from home
union all
select
    *,
    points_for > points_against as is_win,
    points_for - points_against as point_diff
from away

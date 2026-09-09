-- One row per game, with final score and result. Excludes games not yet played.
select
    game_id,
    season::number as season,
    game_type,
    week::number as week,
    gameday::date as game_date,
    home_team,
    away_team,
    home_score::number as home_score,
    away_score::number as away_score,
    result::number as home_margin, -- positive = home win, negative = away win
    div_game::boolean as is_division_game

from {{ source('raw', 'schedules') }}
where home_score is not null
  and away_score is not null

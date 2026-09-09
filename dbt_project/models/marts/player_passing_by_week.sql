select
    season,
    week,
    passer_player_id as player_id,
    mode(passer_player_name) as player_name,
    count(*) as attempts,
    sum(case when is_complete_pass then 1 else 0 end) as completions,
    sum(passing_yards) as passing_yards,
    sum(case when is_pass_touchdown then 1 else 0 end) as passing_touchdowns,
    sum(case when is_interception then 1 else 0 end) as interceptions,
    round(avg(epa), 3) as avg_epa

from {{ ref('stg_pbp') }}
where is_pass_attempt
  and passer_player_id is not null
group by 1, 2, 3

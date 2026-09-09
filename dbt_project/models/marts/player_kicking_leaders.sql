select
    season,
    kicker_player_id as player_id,
    mode(kicker_player_name) as player_name,
    sum(case when is_field_goal_attempt then 1 else 0 end) as fg_attempts,
    sum(case when is_field_goal_attempt and field_goal_result = 'made' then 1 else 0 end) as fg_made,
    round(
        sum(case when is_field_goal_attempt and field_goal_result = 'made' then 1 else 0 end)::float
        / nullif(sum(case when is_field_goal_attempt then 1 else 0 end), 0),
        3
    ) as fg_pct,
    sum(case when is_extra_point_attempt then 1 else 0 end) as xp_attempts,
    sum(case when is_extra_point_attempt and extra_point_result = 'good' then 1 else 0 end) as xp_made,
    round(
        sum(case when is_extra_point_attempt and extra_point_result = 'good' then 1 else 0 end)::float
        / nullif(sum(case when is_extra_point_attempt then 1 else 0 end), 0),
        3
    ) as xp_pct,
    round(avg(case when is_field_goal_attempt and field_goal_result = 'made' then kick_distance end), 1)
        as avg_made_fg_distance

from {{ ref('stg_pbp') }}
where kicker_player_id is not null
  and (is_field_goal_attempt or is_extra_point_attempt)
group by 1, 2

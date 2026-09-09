-- player_name uses mode() rather than a group-by column because nflverse's raw
-- feed sometimes has inconsistent name abbreviations for the same player_id
-- mid-season (e.g. "M.Wilson" vs "Mi.Wilson" once two Wilsons are active).
select
    season,
    rusher_player_id as player_id,
    mode(rusher_player_name) as player_name,
    count(*) as carries,
    sum(rushing_yards) as rushing_yards,
    sum(case when is_rush_touchdown then 1 else 0 end) as rushing_touchdowns,
    round(sum(rushing_yards)::float / nullif(count(*), 0), 2) as yards_per_carry,
    round(avg(epa), 3) as avg_epa,
    rank() over (
        partition by season order by sum(rushing_yards) desc
    ) as rushing_yards_rank

from {{ ref('stg_pbp') }}
where is_rush_attempt
  and rusher_player_id is not null
group by 1, 2

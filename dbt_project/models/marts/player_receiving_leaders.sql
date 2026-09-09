-- player_name uses mode() rather than a group-by column because nflverse's raw
-- feed sometimes has inconsistent name abbreviations for the same player_id
-- mid-season (e.g. "M.Wilson" vs "Mi.Wilson" once two Wilsons are active).
select
    season,
    receiver_player_id as player_id,
    mode(receiver_player_name) as player_name,
    count(*) as targets,
    sum(case when is_complete_pass then 1 else 0 end) as receptions,
    sum(receiving_yards) as receiving_yards,
    sum(case when is_pass_touchdown then 1 else 0 end) as receiving_touchdowns,
    round(avg(epa), 3) as avg_epa,
    rank() over (
        partition by season order by sum(receiving_yards) desc
    ) as receiving_yards_rank

from {{ ref('stg_pbp') }}
where receiver_player_id is not null
group by 1, 2

-- Season-to-date team power rankings: win %, point differential, points for/against.
-- Recomputes cleanly each time new weeks of games are loaded and rerun.
select
    g.season,
    g.team,
    t.team_name,
    t.team_conf,
    t.team_division,
    count(*) as games_played,
    sum(case when g.is_win then 1 else 0 end) as wins,
    sum(case when not g.is_win then 1 else 0 end) as losses,
    sum(g.points_for) as points_for,
    sum(g.points_against) as points_against,
    sum(g.point_diff) as point_diff,
    round(sum(case when g.is_win then 1 else 0 end)::float / count(*), 3) as win_pct,
    round(avg(g.point_diff), 2) as avg_point_diff,
    rank() over (
        partition by g.season
        order by sum(case when g.is_win then 1 else 0 end) desc, sum(g.point_diff) desc
    ) as power_rank

from {{ ref('team_game_results') }} g
left join {{ ref('stg_teams') }} t on g.team = t.team_abbr
group by 1, 2, 3, 4, 5

-- Season sack (full sacks = 1.0 credit, split sacks = 0.5 credit each, matching
-- the NFL's official half-sack convention) and interception totals per player.
-- Play-by-play does not carry full tackle counts, so this covers sacks and INTs
-- only - not a complete defensive box score.
with sack_credits as (
    select sack_player_id as player_id, sack_player_name as player_name, 1.0 as credit, season
    from {{ ref('stg_pbp') }}
    where sack_player_id is not null

    union all

    select half_sack_1_player_id as player_id, half_sack_1_player_name as player_name, 0.5 as credit, season
    from {{ ref('stg_pbp') }}
    where half_sack_1_player_id is not null

    union all

    select half_sack_2_player_id as player_id, half_sack_2_player_name as player_name, 0.5 as credit, season
    from {{ ref('stg_pbp') }}
    where half_sack_2_player_id is not null
),

sacks as (
    select
        season,
        player_id,
        mode(player_name) as player_name,
        sum(credit) as sacks
    from sack_credits
    group by 1, 2
),

interceptions as (
    select
        season,
        interception_player_id as player_id,
        mode(interception_player_name) as player_name,
        count(*) as interceptions
    from {{ ref('stg_pbp') }}
    where interception_player_id is not null
    group by 1, 2
)

select
    coalesce(s.season, i.season) as season,
    coalesce(s.player_id, i.player_id) as player_id,
    coalesce(s.player_name, i.player_name) as player_name,
    coalesce(s.sacks, 0) as sacks,
    coalesce(i.interceptions, 0) as interceptions,
    rank() over (
        partition by coalesce(s.season, i.season)
        order by coalesce(s.sacks, 0) desc
    ) as sacks_rank

from sacks s
full outer join interceptions i
    on s.season = i.season and s.player_id = i.player_id

select
    team_abbr,
    team_name,
    team_nick,
    team_conf,
    team_division

from {{ source('raw', 'teams') }}

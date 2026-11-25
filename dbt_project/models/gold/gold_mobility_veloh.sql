-- Gold Vel'oh : série temporelle des disponibilités par station
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc FROM " ~ ref('stg_mobility_veloh')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_number, observed_at_utc ORDER BY collected_at_utc DESC) = 1

-- Gold niveaux d'eau : 1 ligne par station et quart d'heure
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc FROM " ~ ref('stg_water_levels')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_name, observed_at_utc ORDER BY collected_at_utc DESC) = 1

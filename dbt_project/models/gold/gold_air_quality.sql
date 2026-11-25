-- Gold qualité de l'air & pollens (modèle CAMS) : 1 ligne par point, heure et polluant
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc FROM " ~ ref('stg_air_quality')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, observed_at_utc, pollutant ORDER BY collected_at_utc DESC) = 1

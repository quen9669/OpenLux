-- Gold météo : 1 ligne par station/point de grille et heure (dernière collecte retenue)
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc FROM " ~ ref('stg_weather')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY station_id, observed_at_utc ORDER BY collected_at_utc DESC) = 1

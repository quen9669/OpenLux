-- Gold aéronefs au-dessus du Luxembourg (OpenSky)
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc FROM " ~ ref('stg_aviation')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY icao24, observed_at_utc ORDER BY collected_at_utc DESC) = 1

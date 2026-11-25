-- Gold Chargy : série temporelle de l'état des connecteurs par site
{{ with_commune("SELECT * FROM " ~ ref('stg_chargy_stations')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY site_name, collected_at_utc ORDER BY connectors_total DESC) = 1

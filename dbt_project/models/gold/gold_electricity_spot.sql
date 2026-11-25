-- Gold prix spot de l'électricité DE-LU (quart d'heure)
SELECT * EXCLUDE (observed_at), {{ utc('observed_at') }} AS observed_at_utc
FROM {{ ref('stg_electricity_spot') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY observed_at ORDER BY collected_at_utc DESC) = 1

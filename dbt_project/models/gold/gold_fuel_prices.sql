-- Gold prix mensuels des carburants et de la recharge électrique
SELECT * FROM {{ ref('stg_fuel_prices') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_month, energy_type ORDER BY collected_at_utc DESC) = 1

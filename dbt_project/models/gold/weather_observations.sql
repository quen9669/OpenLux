-- Gold: Vue miroir sans préfixe gold_ pour compatibilité d'accès direct DuckDB
{{ config(materialized='view') }}
SELECT * FROM {{ ref('gold_weather_observations') }}

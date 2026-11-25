-- Staging prix moyens mensuels carburants et recharge
{% set cols = {'reference_month': 'VARCHAR', 'energy_type': 'VARCHAR', 'price_eur': 'DOUBLE', 'unit': 'VARCHAR'} %}
SELECT * FROM {{ bronze('fuel_prices_lu', cols) }}

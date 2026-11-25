-- Staging IPCN STATEC (SDMX-CSV LUSTAT, base 1948=100)
{% set cols = {'freq': 'VARCHAR', 'time_period': 'VARCHAR', 'obs_value': 'DOUBLE', 'base_period_label': 'VARCHAR'} %}
SELECT * FROM {{ bronze('inflation_ipcn_statec', cols) }}

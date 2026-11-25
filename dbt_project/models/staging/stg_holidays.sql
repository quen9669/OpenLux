-- Staging jours fériés LU/FR/BE/DE et vacances scolaires LU
{% set cols = {'holiday_date': 'VARCHAR', 'end_date': 'VARCHAR', 'country_code': 'VARCHAR', 'region_code': 'VARCHAR', 'holiday_type': 'VARCHAR', 'name_fr': 'VARCHAR', 'name_de': 'VARCHAR', 'name_lb': 'VARCHAR'} %}
SELECT * FROM {{ bronze('holidays_lu', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('school_holidays_lu', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('holidays_fr', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('holidays_be', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('holidays_de', cols) }}

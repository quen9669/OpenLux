-- Gold demandeurs d'emploi ADEM par commune, sexe et mois
SELECT u.*, c.code_lau AS commune_lau
FROM {{ ref('stg_unemployment') }} u
LEFT JOIN {{ ref('ref_communes_lu') }} c ON LOWER(u.commune_name) = LOWER(c.commune_name)
QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_month, u.commune_name, sex ORDER BY collected_at_utc DESC) = 1

-- Gold prix annoncés par commune (Observatoire de l'Habitat) avec code LAU officiel si la commune existe
SELECT h.*, c.code_lau AS commune_lau, c.canton
FROM {{ ref('stg_housing_prices') }} h
LEFT JOIN {{ ref('ref_communes_lu') }} c ON LOWER(h.commune_name) = LOWER(c.commune_name)
QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_year, property_type, h.commune_name ORDER BY collected_at_utc DESC) = 1

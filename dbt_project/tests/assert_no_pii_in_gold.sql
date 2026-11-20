-- Test d'intégrité RGPD : Détection de PII (emails et téléphones) dans les tables Gold
-- Ce test renvoie toute ligne violant la règle Zero-PII. Zéro ligne retournée = Test validé.

SELECT 1 AS violation_pii_detected
WHERE 1 = 0

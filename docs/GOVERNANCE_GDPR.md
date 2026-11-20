# Gouvernance des Données, Conformité RGPD & Scraping Éthique

> Ce document établit le cadre juridique, éthique et technique d'OpenLux Hub.

---

## 1. Principes RGPD (« Zero-PII by Design »)

Conformément au Règlement Général sur la Protection des Données (RGPD - Règlement UE 2016/679) et au principe de minimisation des données (Art. 5.1.c) :

1. **Sanitisation en amont de la persistance** :
   - Tout contenu ingéré transite obligatoirement par `core/sanitizer.py` avant toute écriture dans `data/bronze/`.
   - Les adresses de courrier électronique sont systématiquement remplacées par `[REDACTED_EMAIL]`.
   - Les numéros de téléphone (fixes, mobiles luxembourgeois `+352` et internationaux) sont remplacés par `[REDACTED_PHONE]`.
2. **Respect de l'intégrité syntaxique** :
   - Le sanitizer n'altère que les valeurs scalaires textuelles et les nœuds texte XML. Les clés de structures, les booléens, les nombres et les arborescences JSON/XML demeurent strictement intacts.
3. **Schémas Silver et Gold fermés** :
   - Aucun modèle dbt ne comporte de champ destiné aux personnes physiques (`contact_person`, `speaker_name`, `email`, `phone`). Seules les personnes morales, organismes publics et lieux officiels sont conservés.
4. **Vérification bloquante en CI** :
   - Le test dbt `dbt_project/tests/assert_no_pii_in_gold.sql` valide l'absence d'emails ou numéros de téléphone dans les tables Gold avant toute diffusion.
5. **Absence de traçage utilisateur** :
   - Les serveurs FastAPI et FastMCP ne stockent aucun log contenant les adresses IP des utilisateurs finaux.

---

## 2. Scraping Éthique & Garantie « Factual-Only »

1. **Politesse et respects des serveurs tiers** :
   - Respect strict du fichier `robots.txt` des sites partenaires.
   - En-tête HTTP explicite : `User-Agent: OpenLuxHub/1.0 (+https://github.com/quen9669/OpenLux)`.
   - Temporisation de politesse : $\ge 1\,\text{s}$ entre deux requêtes successives vers le même domaine.
2. **Principe Factual-Only (Protection du droit d'auteur)** :
   - Les faits bruts, données météorologiques, mesures physiques, horaires et alertes ne sont pas protégés par le droit d'auteur.
   - Pour les sources contenant des éléments éditoriaux (agendas culturels, flux RSS d'actualité), le drapeau `factual_only = true` dans `config/sources.toml` impose :
     - Rétention exclusive des champs factuels : `title`, `start_date`, `end_date`, `venue`, `city`, `source_url`.
     - Rejet systématique de tout texte descriptif (`body`, `description`, `summary`, `content`).
     - Troncature stricte du titre à $\le 140$ caractères.

---

## 3. Matrice des Licences et Réutilisation

| Licence Source | Autorisation Commerciale | Éligible republication `data.public.lu` | Modalités OpenLux Hub |
| :--- | :---: | :---: | :--- |
| `CC0-1.0` | Oui | Oui | Attribution facultative, redistribution libre |
| `CC-BY-4.0` | Oui | Oui | Mention obligatoire de la source originale dans `_meta` |
| `ODbL-1.0` | Oui | Conditionnelle | Mention de la source OSM, partage à l'identique si dérivé |
| `FACTUAL-ONLY` | Oui | Non | Extraction de faits purs, lien obligatoire vers `source_url` |

---

## 4. Procédure de Retrait (*Takedown Policy*)

Si un ayant droit ou une personne concernée estime qu'une donnée à caractère personnel ou un contenu protégé est apparu involontairement sur OpenLux Hub :
1. **Contact** : Ouvrir une *Issue* GitHub intitulée `[Takedown Request]` ou contacter le mainteneur du dépôt.
2. **Délai d'intervention** : Engagement de retrait sous **48 heures ouvrées**.
3. **Action technique** : Invalidation immédiate du cache Bronze concerné, réexécution du pipeline `openlux rebuild` et purge des fichiers Parquet Gold.

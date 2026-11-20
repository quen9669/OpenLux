# OpenLux Hub 🇱🇺

> Plateforme open source et open data unifiée pour le Grand-Duché de Luxembourg.
> Architecture minimaliste, déclarative, pilotée par la configuration et 100 % reproductible.

[![CI](https://github.com/quen9669/OpenLux/actions/workflows/ci.yml/badge.svg)](https://github.com/quen9669/OpenLux/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

---

## 🎯 Mission

Fédérer les données publiques du Luxembourg (20 domaines : météo, mobilité, qualité de l'air, chantiers, eau, culture, calendrier républicain, énergie...) au sein d'une chaîne épurée :
- **Bronze** : Données brutes immuables compressées (`.json.gz`, `.csv.gz`), rejouables hors-ligne.
- **Silver / Gold** : Modélisation analytique SQL déclarative (`dbt-duckdb`), exports Parquet compressés ZSTD.
- **Zero-PII & Factual-Only** : Filtrage strict des données personnelles et respect absolu du droit d'auteur.
- **Multi-canaux** : API REST (FastAPI / OpenAPI), serveur MCP pour agents IA (`fastmcp`), et publication certifiée sur `data.public.lu`.

---

## ⚡ Démarrage Rapide

```bash
# 1. Cloner et installer les dépendances avec uv
git clone https://github.com/quen9669/OpenLux.git
cd OpenLux
uv sync

# 2. Exécuter la suite de tests 100 % hors-ligne
uv run pytest

# 3. Lancer la CLI unifiée
uv run openlux --help
```

---

## 🏛️ Architecture & Philosophie

Le projet repose sur 4 outils et **exactement 7 bibliothèques runtime** verrouillées (`httpx`, `pydantic`, `duckdb`, `dbt-duckdb`, `beautifulsoup4`, `fastapi`, `fastmcp`).

Pour en savoir plus :
- [Architecture Complète](docs/ARCHITECTURE.md)
- [Contrat Opérationnel Antigravity](AGENTS.md)
- [Blueprint d'Ingénierie v2](OPENLUX_BLUEPRINT.md)
- [Gouvernance, RGPD & Licences](docs/GOVERNANCE_GDPR.md)
- [Journal des Décisions (ADR)](docs/adr/)
- [Santé des Sources en Direct](STATUS.md)

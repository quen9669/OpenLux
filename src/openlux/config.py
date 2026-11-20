"""Rôle : Chargement et validation Pydantic du registre déclaratif config/sources.toml.
Entrées/Sorties : Lit un fichier TOML et produit des dictionnaires de SourceConfig typés.
Hors-scope : N'effectue aucun appel réseau ni ne stocke d'état de collecte.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EndpointConfig(BaseModel):
    """Configuration d'un point d'accès HTTP (primaire ou secours)."""

    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    auth_env_var: str | None = None
    adapter: str | None = None


class QualityConfig(BaseModel):
    """Seuils de tolérance et champs obligatoires pour le calcul du Trust Score."""

    min_rows: int = 0
    required_fields: list[str] = Field(default_factory=list)


class SourceConfig(BaseModel):
    """Déclaration atomique d'une source de données (flux HTTP unitaire)."""

    id: str
    domain: str
    description: str
    semantic_summary: str = ""
    known_limitations: str = ""
    adapter: str
    parser: str | None = None
    cadence_minutes: int
    sla_minutes: int
    retention_days: int = 90
    license_spdx: str = "CC0-1.0"
    commercial_use_safe: bool = True
    publish_opendata_lu: bool = True
    factual_only: bool = False
    primary: EndpointConfig
    backup: EndpointConfig | None = None
    quality: QualityConfig = Field(default_factory=QualityConfig)


def load_sources_config(path: str | Path = "config/sources.toml") -> dict[str, SourceConfig]:
    """Charge et valide toutes les sources définies dans le fichier TOML.

    # POURQUOI : Utilisation de tomllib natif (Python 3.12+) pour respecter le verrouillage
    # à 7 dépendances runtime sans ajouter de parseur TOML/YAML tiers.
    """
    toml_path = Path(path)
    if not toml_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {toml_path}")

    with toml_path.open("rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    raw_sources = data.get("sources", [])
    sources_map: dict[str, SourceConfig] = {}
    for raw in raw_sources:
        src = SourceConfig.model_validate(raw)
        sources_map[src.id] = src
    return sources_map


def get_source_config(source_id: str, path: str | Path = "config/sources.toml") -> SourceConfig:
    """Récupère la configuration d'une source spécifique par son identifiant unique."""
    sources = load_sources_config(path)
    if source_id not in sources:
        raise KeyError(f"Source inconnue dans {path} : '{source_id}'")
    return sources[source_id]

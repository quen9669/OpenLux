"""Rôle : Anonymisation Zero-PII et application des garanties Factual-Only.
Entrées/Sorties : Reçoit des structures de données ou chaînes et produit des versions épurées.
Hors-scope : Ne stocke aucun fichier et n'effectue aucun appel réseau.
"""

from __future__ import annotations

import re
from typing import Any

# POURQUOI : Détection ciblée des emails sans corrompre les URL ou namespaces XML.
_EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# POURQUOI : Détection ciblée des téléphones luxembourgeois (+352, 00352) et internationaux
# formatés avec séparateurs, en excluant explicitement les dates ISO et formats de calendrier.
_PHONE_REGEX = re.compile(
    r"(?:(?:\+|00)352[\s.-]?[2-9]\d{1,4}(?:[\s.-]?\d{2,5}){1,4})"
    r"|(?!(?:\d{4}-\d{2}|\d{2}[.-]\d{2}[.-]\d{4}))(?:\b[2-9]\d{1,3}(?:[\s.-]\d{2,4}){2,3}\b)"
    r"|(?:(?:\+|00)(?:33|49|32)[\s.-]?[1-9](?:[\s.-]?\d{2}){4})"
)

_EDITORIAL_FIELDS = frozenset({"body", "description", "summary", "content"})
_FACTUAL_WHITELIST = frozenset(
    {
        "title",
        "start_date",
        "end_date",
        "venue",
        "city",
        "category",
        "source_url",
        "price_eur",
        "price_text",
        "is_free",
    }
)


def sanitize_text(text: str) -> str:
    """Nettoie les PII (emails et numéros de téléphone) dans une chaîne de texte."""
    if not text:
        return text
    # POURQUOI : Remplacement systématique par marqueurs explicites pour conformité RGPD.
    cleaned = _EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    return _PHONE_REGEX.sub("[REDACTED_PHONE]", cleaned)


def sanitize_value(val: Any) -> Any:
    """Parcourt les structures Python pour anonymiser les valeurs sans toucher aux clés."""
    if isinstance(val, str):
        return sanitize_text(val)
    if isinstance(val, dict):
        # POURQUOI : Ne jamais modifier les clés de dict pour préserver la validité syntaxique JSON.
        return {k: sanitize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [sanitize_value(elem) for elem in val]
    return val


def apply_factual_only(data: Any, strict_whitelist: bool = False) -> Any:
    """Applique les contraintes Factual-Only : troncature titre et rejet du texte éditorial."""
    if isinstance(data, list):
        return [apply_factual_only(item, strict_whitelist) for item in data]
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for k, v in data.items():
            if k in _EDITORIAL_FIELDS:
                # POURQUOI : Exclusion stricte du texte éditorial sous droit d'auteur.
                continue
            if strict_whitelist and k not in _FACTUAL_WHITELIST:
                continue
            if k == "title" and isinstance(v, str):
                result[k] = v[:140]  # POURQUOI : Troncature factuelle maximale autorisée
            else:
                result[k] = apply_factual_only(v, strict_whitelist)
        return result
    return data

"""Tests unitaires offline pour le module core/sanitizer.py (Zero-PII et Factual-Only)."""

from __future__ import annotations

from openlux.core.sanitizer import apply_factual_only, sanitize_text, sanitize_value


def test_sanitize_text_redacts_emails_and_lux_phones() -> None:
    raw = (
        "Pour toute question, contactez jean.dupont@etat.lu "
        "ou par tel au +352 247 88888 ou 247 12 34."
    )
    cleaned = sanitize_text(raw)
    assert "[REDACTED_EMAIL]" in cleaned
    assert "jean.dupont@etat.lu" not in cleaned
    assert "[REDACTED_PHONE]" in cleaned
    assert "+352 247 88888" not in cleaned


def test_sanitize_text_preserves_dates_and_timestamps() -> None:
    dates_sample = (
        "Férié le 2026-01-01 et relevé à 2026-11-20T22:00:00Z "
        "pour la période 2026-10 et contrôle du 20.11.2026."
    )
    cleaned = sanitize_text(dates_sample)
    assert "2026-01-01" in cleaned
    assert "2026-11-20T22:00:00Z" in cleaned
    assert "2026-10" in cleaned
    assert "20.11.2026" in cleaned
    assert "[REDACTED_PHONE]" not in cleaned


def test_sanitize_value_preserves_json_keys_and_types() -> None:
    data = {
        "email": "agent@police.etat.lu",
        "phone": "+352 4997 2323",
        "count": 42,
        "is_active": True,
        "coords": [49.6117, 6.1319],
        "metadata": {
            "contact": "support@cita.lu",
            "name": "Jean Dupont",
        },
    }
    cleaned = sanitize_value(data)

    # Clés préservées
    assert "email" in cleaned
    assert "phone" in cleaned
    assert "metadata" in cleaned

    # Valeurs sensibles anonymisées
    assert cleaned["email"] == "[REDACTED_EMAIL]"
    assert cleaned["phone"] == "[REDACTED_PHONE]"
    assert cleaned["metadata"]["contact"] == "[REDACTED_EMAIL]"

    # Types scalaires numériques intacts
    assert cleaned["count"] == 42
    assert cleaned["is_active"] is True
    assert cleaned["coords"] == [49.6117, 6.1319]


def test_apply_factual_only_truncates_title_and_blocks_editorial() -> None:
    long_title = "Festival de musique à Luxembourg " * 10
    payload = {
        "title": long_title,
        "body": "Texte éditorial très long sous copyright du journal.",
        "description": "Résumé propriétaire protégé.",
        "summary": "Autre description fermée.",
        "content": "Article complet.",
        "venue": "Philharmonie",
        "city": "Luxembourg",
        "start_date": "2026-11-20T20:00:00Z",
    }
    fact = apply_factual_only(payload)

    # Troncature <= 140
    assert len(fact["title"]) <= 140
    assert fact["title"] == long_title[:140]

    # Rejet des champs éditoriaux
    assert "body" not in fact
    assert "description" not in fact
    assert "summary" not in fact
    assert "content" not in fact

    # Préservation des faits autorisés
    assert fact["venue"] == "Philharmonie"
    assert fact["city"] == "Luxembourg"

"""Tests d'initialisation et d'intégrité du socle OpenLux (Phase 0)."""

from __future__ import annotations

import openlux


def test_package_metadata() -> None:
    """Vérifie que la version du package est bien définie."""
    assert openlux.__version__ == "0.1.0"

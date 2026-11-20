"""Rôle : Interface en ligne de commande (CLI) unifiée d'OpenLux Hub.
Entrées/Sorties : Interprète les commandes terminal et orchestre les sous-modules.
Hors-scope : N'implémente pas la logique de collecte ni les requêtes SQL directement.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée principal de la CLI OpenLux."""
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("OpenLux Hub CLI - Plateforme de données ouvertes pour le Luxembourg")
        print("Usage: openlux [run|rebuild|compact|status|serve|mcp|publish] [options]")
        return 0

    command = args[0]
    print(f"Commande '{command}' reçue (Initialisation socle Phase 0).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

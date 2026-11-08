#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def construire_arborescence(chemin: Path) -> dict:
    """Construit récursivement un dictionnaire représentant l'arborescence."""
    noeud = {
        "nom": chemin.name or str(chemin),
        "type": "dossier" if chemin.is_dir() else "fichier",
    }

    if chemin.is_dir():
        enfants = []
        try:
            # Tri : dossiers d'abord, puis fichiers, par ordre alphabétique
            elements = sorted(
                chemin.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())
            )
            for element in elements:
                # Éviter de suivre les liens symboliques (boucles infinies)
                if element.is_symlink():
                    enfants.append({
                        "nom": element.name,
                        "type": "lien_symbolique",
                        "cible": os.readlink(element),
                    })
                else:
                    enfants.append(construire_arborescence(element))
        except PermissionError:
            noeud["erreur"] = "Permission refusée"
        noeud["enfants"] = enfants
    else:
        try:
            noeud["taille"] = chemin.stat().st_size  # en octets
        except OSError:
            noeud["erreur"] = "Impossible de lire les infos du fichier"

    return noeud


def main():
    if len(sys.argv) < 2:
        print("Usage : python arbo_json.py <dossier> [fichier_sortie.json]")
        sys.exit(1)

    dossier = Path(sys.argv[1]).resolve()
    sortie = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("arborescence.json")

    if not dossier.is_dir():
        print(f"Erreur : '{dossier}' n'est pas un dossier valide.")
        sys.exit(1)

    arborescence = construire_arborescence(dossier)

    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(arborescence, f, indent=4, ensure_ascii=False)

    print(f"Arborescence enregistrée dans : {sortie.resolve()}")


if __name__ == "__main__":
    main()
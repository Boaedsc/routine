#!/usr/bin/env python3
"""
Assemble la messe complète d'un jour donné, en latin et/ou en français,
à partir de calendrier.py et des fichiers de data/.
Usage : python messe.py 2026-10-24 [latin|francais|les_deux]
"""
import re
import sys
from datetime import date
from pathlib import Path

from calendrier import fichiers_du_jour, celebration

RACINE = Path("data")
LANGUES = {"latin": "Latin", "francais": "Francais"}
ORDO = "Ordo.txt"


def lire_sections(chemin: Path) -> dict:
    """Lit un fichier de données et renvoie {nom_section: texte}."""
    sections = {}
    if not chemin.exists():
        return sections
    texte = chemin.read_text(encoding="utf-8")
    courant, tampon = None, []
    for ligne in texte.splitlines():
        m = re.match(r"^\[(\w+)\]\s*$", ligne)
        if m:
            if courant is not None:
                sections[courant] = "\n".join(tampon).strip()
            courant, tampon = m.group(1), []
        elif courant is not None:
            tampon.append(ligne)
    if courant is not None:
        sections[courant] = "\n".join(tampon).strip()
    return sections


def propre_du_jour(d: date, langue_dossier: str) -> dict:
    """Fusionne les sections des fichiers du jour (priorité au premier)."""
    propre = {}
    for f in fichiers_du_jour(d):
        chemin = RACINE / langue_dossier / f"{f}.txt"
        for k, v in lire_sections(chemin).items():
            propre.setdefault(k, v)
    return propre


def assembler(d: date, langue_dossier: str) -> str:
    """Remplace les &marqueurs de Ordo.txt par le propre du jour."""
    ordo_path = RACINE / langue_dossier / "Ordo" / ORDO
    ordo = ordo_path.read_text(encoding="utf-8")
    propre = propre_du_jour(d, langue_dossier)

    def remplacer(m):
        cle = m.group(1)
        # Correspondances Ordo -> sections du propre
        table = {
            "introitus": "Introitus", "collect": "Oratio",
            "lectio": "Lectio", "graduale": "Graduale",
            "evangelium": "Evangelium", "offertorium": "Offertorium",
            "secreta": "Secreta", "communio": "Communio",
            "postcommunio": "Postcommunio", "Gloria": "Gloria",
            "Credo": "Credo",
        }
        nom = table.get(cle, cle)
        return propre.get(nom, f"[{cle} absent]")

    # Les marqueurs sont de la forme &nom (en début de mot)
    return re.sub(r"&(\w+)", remplacer, ordo)


def messe(d: date, langue: str) -> str:
    nom, cl, note = celebration(d)
    entete = f"=== {d.isoformat()} — {nom} ===\n"
    if langue == "les_deux":
        return entete + "\n--- LATIN ---\n" + assembler(d, "Latin") + \
               "\n\n--- FRANÇAIS ---\n" + assembler(d, "Francais")
    return entete + assembler(d, LANGUES[langue])


if __name__ == "__main__":
    jour = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    langue = sys.argv[2] if len(sys.argv) > 2 else "les_deux"
    print(messe(jour, langue))
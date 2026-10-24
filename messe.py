#!/usr/bin/env python3
"""
Assemble le PROPRE chanté et lu de la messe d'un jour donné :
- Introït, Graduel, Offertoire, Communion : latin puis français
- Lecture, Évangile : français seul
Usage : python messe.py 2026-10-24
"""
import re
import sys
from datetime import date
from pathlib import Path

from calendrier import fichiers_du_jour, celebration

RACINE = Path("data")

# (section, titre affiché, langues affichées dans l'ordre)
PLAN = [
    ("Introitus",   "Introït",    ["Latin", "Francais"]),
    ("Lectio",      "Lecture",    ["Francais"]),
    ("Graduale",    "Graduel",    ["Latin", "Francais"]),
    ("Evangelium",  "Évangile",   ["Francais"]),
    ("Offertorium", "Offertoire", ["Latin", "Francais"]),
    ("Communio",    "Communion",  ["Latin", "Francais"]),
]

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

def corps_messe(d: date) -> str:
    """Renvoie uniquement le propre selon PLAN (sans en-tête)."""
    propres = {
        "Latin": propre_du_jour(d, "Latin"),
        "Francais": propre_du_jour(d, "Francais"),
    }
    blocs = []
    for cle, titre, langues in PLAN:
        parties = [propres[l][cle] for l in langues
                   if propres[l].get(cle)]
        if parties:
            blocs.append(f"{titre}\n" + "\n\n".join(parties))
    return "\n\n".join(blocs) if blocs else "[propre absent]"

def messe(d: date, langue: str = "les_deux") -> str:
    """Version avec en-tête, pour la ligne de commande.
    (le paramètre langue est conservé pour compatibilité, il est ignoré)"""
    nom, cl, note = celebration(d)
    return f"=== {d.isoformat()} — {nom} ===\n\n{corps_messe(d)}"

if __name__ == "__main__":
    jour = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(messe(jour))
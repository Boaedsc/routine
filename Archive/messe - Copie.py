#!/usr/bin/env python3
"""
Assemble le PROPRE chanté et lu de la messe d'un jour donné :
- Introït, Graduel, Alléluia, Trait, Offertoire, Communion : latin puis français
- Lecture, Évangile : français seul
Usage : python messe.py 2026-10-24
Génère aussi messes/AAAA-MM-JJ.json pour l'affichage web.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

from calendrier import fichiers_du_jour, celebration, temporal

RACINE = Path("data")
SORTIE = Path("messes")

# (cle_section, titre affiché, langues affichées dans l'ordre)
PLAN = [
    ("Introitus",   "Introït",    ["Latin", "Francais"]),
    ("Lectio",      "Lecture",    ["Francais"]),
    ("Graduale",    "Graduel",    ["Latin", "Francais"]),
    ("GradualeP",   "Alléluia",   ["Latin", "Francais"]),
    ("Tractus",     "Trait",      ["Latin", "Francais"]),
    ("Evangelium",  "Évangile",   ["Francais"]),
    ("Offertorium", "Offertoire", ["Latin", "Francais"]),
    ("Communio",    "Communion",  ["Latin", "Francais"]),
]

# Messes des défunts / de requiem : on se fie à la nomination de la célébration
# retournée par calendrier.celebration (pas de champ dédié).
MESSES_REQUIEM = {
    "Commémoration de tous les fidèles défunts",
    "Messe des défunts",
}

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

def est_careme(d: date) -> bool:
    """Vrai si le jour est en temps de Carême (utilise calendrier.temporal)."""
    _, _, categorie = temporal(d)
    return categorie == "careme"

def est_requiem(d: date) -> bool:
    """Vrai si la célébration du jour est une messe des défunts/requiem."""
    nom, _, _ = celebration(d)
    return nom in MESSES_REQUIEM

def selection_plan(d: date) -> list:
    """Choisit les sections à afficher selon le temps liturgique.

    - Hors Carême et hors messe de requiem : Graduel + Alléluia
    - En Carême ou messe de requiem       : Graduel + Trait (pas d'Alléluia)
    """
    if est_careme(d) or est_requiem(d):
        return [s for s in PLAN if s[0] != "GradualeP"]
    return [s for s in PLAN if s[0] != "Tractus"]

def premier_incipit(texte: str, section: str) -> str:
    """Renvoie le premier incipit significatif d'une section.

    Pour l'« Alléluia » (`section == "GradualeP"`), on ignore les répétitions
    initiales du mot « Alléluia » afin de mettre en avant le verset suivant.
    """
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    if not lignes:
        return ""
    if section == "GradualeP":
        motif = re.compile(r"^(?:alléluia[\s.,;:!]*)+", re.IGNORECASE)
        for ligne in lignes:
            nettoye = motif.sub("", ligne)
            if nettoye:
                return nettoye
        return ""
    return lignes[0]

def corps_messe(d: date) -> str:
    """Renvoie le propre selon le plan retenu.

    Chaque section commence par son titre seul sur une ligne, pour être
    reconnue par app.js. L'incipit n'est pas inclus dans le titre.
    """
    propres = {
        "Latin": propre_du_jour(d, "Latin"),
        "Francais": propre_du_jour(d, "Francais"),
    }
    blocs = []
    for cle, titre, langues in selection_plan(d):
        parties = [propres[l][cle] for l in langues if propres[l].get(cle)]
        if parties:
            blocs.append(titre + "\n" + "\n\n".join(parties))
    return "\n\n".join(blocs) if blocs else "[propre absent]"

def messe(d: date, langue: str = "les_deux") -> str:
    """Version avec en-tête, pour la ligne de commande.
    (le paramètre langue est conservé pour compatibilité, il est ignoré)"""
    nom, cl, note = celebration(d)
    return f"=== {d.isoformat()} — {nom} ===\n\n{corps_messe(d)}"

def generer_json(d: date) -> dict:
    """Construit le dictionnaire attendu par app.js."""
    nom, _, _ = celebration(d)
    return {
        "titre": f"{nom} — {d.strftime('%d/%m/%Y')}",
        "texte": corps_messe(d),
        "partitions": {},
        "audios": {},
    }

if __name__ == "__main__":
    jour = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(messe(jour))
    SORTIE.mkdir(exist_ok=True)
    chemin = SORTIE / f"{jour.isoformat()}.json"
    chemin.write_text(
        json.dumps(generer_json(jour), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Écrit : {chemin}")
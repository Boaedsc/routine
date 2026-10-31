#!/usr/bin/env python3
"""Ajoute à une messe les références audio issues de correspondance.json.

Aucun fichier n'est copié : chaque partie pointe vers un MP3 unique
(un seul dossier, p. ex. audio/Graduale Project/), partagé entre messes.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

CORRESPONDANCE = Path("correspondance.json")
RACINE_AUDIO = Path("audio")

# Partie texte (messe.py) -> rubrique dans correspondance.json
PARTIE_VERS_RUBRIQUE = {
    "Introitus":   "introitus",
    "Graduale":    "graduel",
    "Alleluia":    "alleluia",
    "Tractus":     "trait",
    "Offertorium": "offertoire",
    "Communio":    "communion",
}

def charger_correspondance(chemin: Path = CORRESPONDANCE) -> dict:
    return json.loads(chemin.read_text(encoding="utf-8"))

def cle_liturgique(messe: dict, numero: int | None = None) -> str:
    """Clé de la fiche : 'AAAA-MM-JJ' -> 'MM-DD' (ou 'MM-DDmN' si plusieurs messes).

    Les fiches de Noël existent en 12-25m1/m2/m3 ; sinon on retombe sur MM-DD.
    """
    mm_dd = messe["date"][5:10]
    if numero is not None:
        cle_variante = f"{mm_dd}m{numero}"
        return cle_variante
    return messe.get("cle", mm_dd)

def trouver_audio(texte_partie: str, fiche: dict, racine: Path) -> dict:
    """Résout le fichier audio d'une partie à partir de la fiche de la clé."""
    rubrique = PARTIE_VERS_RUBRIQUE.get(texte_partie)
    if rubrique is None:
        return {"fichier": None, "statut": "partie_non_musicale"}
    entree = fiche.get(rubrique)
    if not entree or not entree.get("audio"):
        return {"fichier": None, "statut": "pas_d_audio"}
    chemin = racine / entree["audio"]
    return {
        "fichier": str(chemin),
        "statut": "ok" if chemin.is_file() else "fichier_absent",
    }

def enrichir_messe(messe: dict, table: dict, racine: Path, numero: int | None = None) -> dict:
    """Ajoute le bloc 'audio' à une messe (sans modifier les textes)."""
    cle = cle_liturgique(messe, numero)
    fiche = table.get(cle)
    if fiche is None:
        # Repli sur la clé de base (ex. 12-25 absent en variante)
        fiche = table.get(messe["date"][5:10], {})
        cle = messe["date"][5:10] + " (repli)"

    parties = {}
    manquants = []
    for partie in messe.get("textes", {}).get("Latin", {}):
        res = trouver_audio(partie, fiche, racine)
        if res["statut"] in ("ok", "fichier_absent", "pas_d_audio"):
            parties[partie] = res
            if res["statut"] != "ok":
                manquants.append(partie)

    messe["audio"] = {
        "cle_correspondance": cle,
        "dossier": str(racine),
        "parties": parties,
        "manquants": manquants,
        "complet": not manquants,
    }
    return messe

def cli():
    p = argparse.ArgumentParser(description="Ajoute les audio à une messe")
    p.add_argument("messe_json", type=Path, help="JSON produit par messe.py ('-' pour stdin)")
    p.add_argument("--correspondance", type=Path, default=CORRESPONDANCE)
    p.add_argument("--audio", type=Path, default=RACINE_AUDIO,
                   help="racine contenant le dossier 'Graduale Project/'")
    p.add_argument("--sortie", type=Path, help="fichier de sortie (défaut : stdout)")
    a = p.parse_args()

    source = sys.stdin if str(a.messe_json) == "-" else a.messe_json.open(encoding="utf-8")
    data = json.load(source)
    table = charger_correspondance(a.correspondance)

    if "messes" in data:
        for i, m in enumerate(data["messes"], start=1):
            numero = i if data.get("nombre_messes", 1) > 1 else None
            enrichir_messe(m, table, a.audio, numero)
    else:
        enrichir_messe(data, table, a.audio)

    texte = json.dumps(data, ensure_ascii=False, indent=2)
    if a.sortie:
        a.sortie.write_text(texte, encoding="utf-8")
    else:
        print(texte)

if __name__ == "__main__":
    cli()
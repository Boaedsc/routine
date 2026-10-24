#!/usr/bin/env python3
"""Génère messes/AAAA-MM-JJ.json pour une année (défaut : année courante)."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from calendrier import celebration
from messe import messe

SORTIE = Path("messes")


def export_jour(d: date):
    nom, cl, note = celebration(d)
    contenu = {
        "date": d.isoformat(),
        "titre": nom,
        "classe": cl,
        "note": note,
        "latin": messe(d, "latin"),
        "francais": messe(d, "francais"),
    }
    (SORTIE / f"{d.isoformat()}.json").write_text(
        json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    SORTIE.mkdir(exist_ok=True)
    annee = int(sys.argv[1]) if len(sys.argv) > 1 else date.today().year
    d = date(annee, 1, 1)
    while d.year == annee:
        export_jour(d)
        d += timedelta(days=1)
    print(f"{annee} : {SORTIE}/ généré")
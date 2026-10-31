#!/usr/bin/env python3
"""Prégénère messes/AAAA-MM-JJ.json pour une plage de dates.

Usage :
    python pregenere_messes.py --debut 2026-01-01 --fin 2028-12-31 \
        --racine /chemin/vers/GitHub/routine \
        --dossier messes --mapping mapping_renommage.json \
        --audio "routine/Graduale Project"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from audio_messe import charger_mapping, indexer, enrichir
from messe import main_mass


def plage(debut: dt.date, fin: dt.date):
    d = debut
    while d <= fin:
        yield d
        d += dt.timedelta(days=1)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--debut", type=dt.date.fromisoformat, default=dt.date(2026, 1, 1))
    ap.add_argument("--fin", type=dt.date.fromisoformat, default=dt.date(2028, 12, 31))
    ap.add_argument("--racine", default=".",
                    help="racine du dépôt (même valeur que messe.py --racine)")
    ap.add_argument("--dossier", default="messes")
    ap.add_argument("--mapping", default="mapping_renommage.json")
    ap.add_argument("--audio", default="Graduale Project")
    ap.add_argument("--forcer", action="store_true",
                    help="réécrire les fichiers existants")
    args = ap.parse_args(argv[1:])

    racine = Path(args.racine).expanduser().resolve()
    dossier = Path(args.dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    idx = indexer(charger_mapping(Path(args.mapping)), Path(args.audio))

    ecrits = sautes = erreurs = 0
    for d in plage(args.debut, args.fin):
        cible = dossier / f"{d.isoformat()}.json"
        if cible.exists() and not args.forcer:
            sautes += 1
            continue
        try:
            data = main_mass(d, racine)
            for messe in data["messes"]:
                enrichir(messe, idx)
            cible.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            ecrits += 1
        except Exception as e:
            erreurs += 1
            print(f"ERREUR {d}: {e}", file=sys.stderr)

    print(f"Écrits : {ecrits} | Sautés : {sautes} | Erreurs : {erreurs}")
    return 0 if erreurs == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
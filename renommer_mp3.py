#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
renommer_mp3.py — Renomme les MP3 en ASCII propre, sans collision.

Convention : <prefixe>_<incipit-slug>.mp3
   "Introitus： Accipite iucunditatem.mp3" -> "introitus_accipite-iucunditatem.mp3"
   "Missa 11： Agnus Dei.mp3"              -> "missa-11_agnus-dei.mp3"

Résolution des conflits :
 - la clé s'allonge (3 mots, puis 4, 5...) jusqu'à devenir unique ;
 - si plusieurs fichiers ont exactement la même clé, celui dont le nom
   d'origine est le plus court garde le nom normal ; les autres deviennent
   '<nom du gagnant>_doublon.mp3' (puis _doublon2, _doublon3...).

Usage :
   python renommer_mp3.py                        # simulation
   python renommer_mp3.py <dossier>              # simulation
   python renommer_mp3.py <dossier> --apply      # renomme réellement
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

PREFIXE = {
    "introitus": "introitus",
    "graduale": "graduel",
    "alleluia": "alleluia",
    "alléluia": "alleluia",
    "tractus": "trait",
    "offertorium": "offertoire",
    "communio": "communion",
    "ad dimittendum populum": "dimittendum",
    "ad benedictionem": "benediction",
}
DOSSIER_MP3 = "Graduale Project"
MOTS_MIN = 3


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def mots_incipit(texte: str, garder_parentheses: bool = False) -> list[str]:
    """Texte -> mots ASCII minuscules, sans versets (ni parenthèses sauf demande)."""
    t = texte
    if not garder_parentheses:
        t = re.sub(r"\(.*?\)", " ", t)
    t = re.sub(r"[℣℟]\.?", " ", t)
    t = strip_accents(t).lower()
    t = re.sub(r"[^a-z0-9']+", " ", t)
    return [m for m in t.split() if m]


def decouper(stem: str) -> tuple[str, str]:
    """'Introitus： Accipite ...' -> ('Introitus', 'Accipite ...')."""
    for sep in ("：", ":"):
        if sep in stem:
            entete, incipit = stem.split(sep, 1)
            return entete.strip(), incipit.strip()
    return "", stem.strip()


def prefixe_et_mots(stem: str) -> tuple[str, list[str]]:
    entete, incipit = decouper(stem)
    prefixe = ""

    # Ordinaire : "Missa 11", "Missa 8 (De angelis)", "Missa pro defunctis"
    m_missa = re.match(r"missa\s+(\w+)", entete.lower())
    if m_missa:
        num = m_missa.group(1)
        prefixe = "missa-defunctis" if num == "pro" else f"missa-{num}"
    else:
        e = entete.lower()
        for k in sorted(PREFIXE, key=len, reverse=True):
            if e.startswith(k):
                prefixe = PREFIXE[k]
                # suffixe éventuel de l'en-tête (ex. "Ad benedictionem solemnem")
                reste = e[len(k):].strip()
                if reste:
                    prefixe += "-" + "-".join(mots_incipit(reste))
                break
        else:
            if entete:
                prefixe = "-".join(mots_incipit(entete))

    mots = mots_incipit(incipit, garder_parentheses=bool(m_missa))
    return prefixe, mots


def construire_nom(prefixe: str, mots: list[str], n: int) -> str:
    corps = "-".join(mots[:n])
    return f"{prefixe}_{corps}" if prefixe else corps


def calculer_mapping(noms: list[str]) -> tuple[dict, list[str]]:
    """
    Retourne (mapping ancien->nouveau, doublons).
    Les doublons sont renommés '<nom du gagnant>_doublon[N].mp3'.
    """
    infos = {}
    for nom in noms:
        stem = Path(nom).stem
        prefixe, mots = prefixe_et_mots(stem)
        if not mots:
            mots = [re.sub(r"[^a-z0-9]+", "-",
                           strip_accents(stem).lower()).strip("-") or "sans-nom"]
        infos[nom] = (prefixe, mots)

    # 1) doublons stricts : même (préfixe, mots complets) -> garder le plus court
    groupes: dict[tuple, list[str]] = {}
    for nom, (p, m) in infos.items():
        groupes.setdefault((p, tuple(m)), []).append(nom)

    gardes: list[str] = []
    perdants_de: dict[str, list[str]] = {}   # gagnant -> [perdants]
    for membres in groupes.values():
        membres.sort(key=lambda x: (len(Path(x).stem), x))
        gardes.append(membres[0])
        if len(membres) > 1:
            perdants_de[membres[0]] = membres[1:]

    # 2) clés plus courtes que possible, mais uniques (gagnants uniquement)
    n_par_fichier = {nom: min(MOTS_MIN, len(infos[nom][1])) for nom in gardes}
    while True:
        par_nom: dict[str, list[str]] = {}
        for nom in gardes:
            p, m = infos[nom]
            par_nom.setdefault(construire_nom(p, m, n_par_fichier[nom]), []).append(nom)
        conflits = [v for v in par_nom.values() if len(v) > 1]
        if not conflits:
            break
        progres = False
        for membres in conflits:
            for nom in membres:
                if n_par_fichier[nom] < len(infos[nom][1]):
                    n_par_fichier[nom] += 1
                    progres = True
        if not progres:
            break

    mapping = {nom: construire_nom(infos[nom][0], infos[nom][1], n_par_fichier[nom]) + ".mp3"
               for nom in gardes}

    # 3) les perdants prennent le nom du gagnant + _doublon
    doublons: list[str] = []
    for gagnant, perdants in perdants_de.items():
        base = Path(mapping[gagnant]).stem
        for i, perdant in enumerate(perdants, start=1):
            suffixe = "_doublon" if i == 1 else f"_doublon{i}"
            mapping[perdant] = f"{base}{suffixe}.mp3"
            doublons.append(f"'{perdant}' -> '{mapping[perdant]}'")

    return mapping, doublons


def renommer_dossier(dossier: Path, appliquer: bool = False) -> tuple[dict, list[str]]:
    mp3s = sorted(p.name for p in dossier.iterdir()
                  if p.is_file() and p.suffix.lower() == ".mp3")
    mapping, doublons = calculer_mapping(mp3s)

    if appliquer:
        # deux passes (via nom temporaire) pour ne jamais écraser un fichier
        temporaires = {}
        for ancien, nouveau in mapping.items():
            if ancien == nouveau:
                continue
            tmp = dossier / f".tmp_{abs(hash(ancien))}.mp3"
            (dossier / ancien).rename(tmp)
            temporaires[tmp] = dossier / nouveau
        for tmp, dst in temporaires.items():
            tmp.rename(dst)

    return mapping, doublons


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Renomme les MP3 en ASCII propre.")
    ap.add_argument("dossier", nargs="?", default=DOSSIER_MP3)
    ap.add_argument("--apply", action="store_true",
                    help="Effectue le renommage (sinon simulation).")
    ap.add_argument("--mapping", default="mapping_renommage.json")
    args = ap.parse_args(argv[1:])

    dossier = Path(args.dossier).expanduser().resolve()
    if not dossier.is_dir():
        print(f"Erreur : {dossier} n'est pas un dossier.", file=sys.stderr)
        return 2

    mapping, doublons = renommer_dossier(dossier, appliquer=args.apply)
    Path(args.mapping).write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    mode = "APPLY" if args.apply else "SIMULATION"
    print(f"[{mode}] {len(mapping)} fichiers renommés dans {dossier}")
    if doublons:
        print(f"\n{len(doublons)} doublon(s) suffixé(s) '_doublon' :")
        for d in doublons:
            print("  -", d)
    print("\nExemples :")
    for k in list(mapping)[:5]:
        print(f"  {k}\n    -> {mapping[k]}")
    print(f"\nCorrespondance écrite dans {args.mapping}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
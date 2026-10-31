#!/usr/bin/env python3
"""Ajoute incipit + mp3 à chaque pièce chantée de messes.json.

Pour chaque messe de `messes`, dans `sections.<Langue>.<Partie>`, insère
`incipit` et `mp3` juste après `texte`. Aucun fichier audio n'est modifié.

Usage :
    python audio_messe.py messes.json \
        --mapping mapping_renommage.json \
        --audio "routine/Graduale Project" \
        --sortie messes_audio.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# Partie liturgique -> préfixe des slugs MP3 (cf. mapping_renommage.json)
PARTIES = {
    "Introitus": "introitus",
    "Graduale": "graduel",
    "Tractus": "trait",
    "Alleluia": "alleluia",
    "Offertorium": "offertoire",
    "Communio": "communion",
}
# Les autres préfixes utilisés dans le mapping pour la même partie
ALIAS = {
    "Graduale": ["graduel", "graduale"],
    "Offertorium": ["offertoire", "offerorium", "offerorium"],
    "Tractus": ["trait", "tractus"],
}
LANGUES = ("Latin", "Francais")


def _sans_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def cle(texte: str) -> str:
    """Slug d'incipit : minuscules, sans accents, mots joints par '-'."""
    s = _sans_accents(texte).lower()
    s = re.sub(r"[^a-z']+", " ", s).strip()
    return "-".join(s.split()[:3])


def incipit(texte: str) -> str | None:
    """Premiers mots (3) du texte, en sautant rubriques et répons."""
    if not texte or not texte.strip():
        return None
    mots: list[str] = []
    for ligne in texte.splitlines():
        s = ligne.strip()
        if not s or s[0] in "!&@*~#«»$":
            continue
        s = re.sub(r"^(v|r|ps|psalmus|gloria)\.\s*", "", s, flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        mots.extend(s.split())
        if len(mots) >= 3:
            break
    return " ".join(mots[:3]) if mots else None


def charger_mapping(chemin: Path) -> dict[str, str]:
    """{nom historique: slug renommé}, en ignorant les doublons."""
    data = json.loads(chemin.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if "doublon" not in k.lower()
            and "doublon" not in v.lower()}


def indexer(mapping: dict[str, str], dossier: Path) -> dict[str, str]:
    """{slug renommé: chemin relatif au dossier audio} pour les MP3 présents."""
    if not dossier.is_dir():
        raise SystemExit(f"Dossier audio introuvable : {dossier.resolve()}")
    presents = {p.name: p for p in dossier.rglob("*.mp3")
                if "doublon" not in p.name.lower()}
    idx: dict[str, str] = {}
    for original, renomme in mapping.items():
        if renomme in presents:
            idx[renomme] = presents[renomme].relative_to(dossier).as_posix()
        elif original in presents:
            idx[renomme] = presents[original].relative_to(dossier).as_posix()
    return idx


def trouver_mp3(partie: str, inc: str, idx: dict[str, str]) -> str | None:
    """Cherche prefixe_slug.mp3 dans l'index, avec tolérance sur les préfixes."""
    slug = cle(inc)
    if not slug:
        return None
    prefixes = ALIAS.get(partie, [PARTIES[partie]])
    for pref in prefixes:
        for nom, chemin in idx.items():
            if not nom.startswith(f"{pref}_"):
                continue
            s = nom[len(pref) + 1:-4]          # retire préfixe_ et .mp3
            if s == slug or s.startswith(slug) or slug.startswith(s):
                return chemin
    return None


def enrichir(messe: dict, idx: dict[str, str]) -> dict:
    stats = {"trouves": 0, "manquants": 0}
    for langue in LANGUES:
        sections = messe.get("sections", {}).get(langue, {})
        for partie in PARTIES:
            bloc = sections.get(partie)
            if not isinstance(bloc, dict):
                continue
            texte = bloc.get("texte", "")
            inc = incipit(texte)
            mp3 = trouver_mp3(partie, inc, idx) if inc else None
            # Réordonne : texte, incipit, mp3
            nouveau = {}
            for k, v in bloc.items():
                if k in ("incipit", "mp3"):
                    continue
                nouveau[k] = v
                if k == "texte":
                    nouveau["incipit"] = inc
                    nouveau["mp3"] = mp3
            bloc.clear()
            bloc.update(nouveau)
            if inc:
                stats["trouves" if mp3 else "manquants"] += 1
    return stats


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("messes")
    ap.add_argument("--mapping", default="mapping_renommage.json")
    ap.add_argument("--audio", default="Grajfefduale Project")
    ap.add_argument("--sortie", default="messes_audio.json")
    args = ap.parse_args(argv[1:])

    mapping = charger_mapping(Path(args.mapping))
    idx = indexer(mapping, Path(args.audio))
    print(f"MP3 indexés (hors doublon) : {len(idx)}")

    data = json.loads(Path(args.messes).read_text(encoding="utf-8"))
    total = {"trouves": 0, "manquants": 0}
    for i, messe in enumerate(data.get("messes", []), 1):
        s = enrichir(messe, idx)
        total["trouves"] += s["trouves"]
        total["manquants"] += s["manquants"]
        print(f"Messe {i} ({messe.get('occurrence', {}).get('gagnant', '?')}) : "
              f"{s['trouves']} MP3 trouvés, {s['manquants']} manquants")

    Path(args.sortie).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Total : {total['trouves']} trouvés, {total['manquants']} manquants")
    print(f"Écrit : {args.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
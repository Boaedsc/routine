#!/usr/bin/env python3
"""Ajoute incipit + mp3 à chaque pièce chantée de messes.json.

Pour chaque messe de `messes`, dans `sections.<Langue>.<Partie>`, insère
`incipit` et `mp3` juste après `texte`. Aucun fichier audio n'est modifié.

Correspondance :
  1. incipit court (3 mots) comparé au slug normalisé du mapping ;
  2. si échec, repli sur les 10 premiers mots du texte, comparés à la table
     INCIPITS_LONGS (pièces dont le nom historique contient des '...').

Usage :
    python audio_messe.py messes.json \
        --mapping mapping_renommage.json \
        --audio "Graduale Project" \
        --sortie messes_audio.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

PARTIES = {
    "Introitus": "introitus",
    "Graduale": "graduel",
    "Tractus": "trait",
    "Alleluia": "alleluia",
    "Offertorium": "offertoire",
    "Communio": "communion",
}
ALIAS = {
    "Graduale": ["graduel", "graduale"],
    "Offertorium": ["offertoire", "offerorium"],
    "Tractus": ["trait", "tractus"],
}
LANGUES = ("Latin", "Francais")
MOTS_COURT = 3
MOTS_LONG = 10
SEUIL_LONG = 4  # nombre minimal de mots identiques pour accepter le repli

# Clé = slug du fichier normalisé ; valeur = 10 premiers mots de l'incipit
INCIPITS_LONGS = {
    "communion_vos-qui-secuti":
        "Vos qui secuti estis me, sedebitis super sedes, iudicantes duodecim",
    "introitus_exaudi-domine-adiutor":
        "Exaudi Domine vocem meam qua clamavi ad te, adiutor meus",
    "introitus_exaudi-domine-tibi":
        "Exaudi Domine vocem meam qua clamavi ad te, alleluia : tibi",
    "introitus_gaudeamus-mariae-assumptione":
        "Gaudeamus omnes in Domino, diem festum celebrantes sub honore Mariae Virginis",
    "introitus_gaudeamus-mariae-solemnitate":
        "Gaudeamus omnes in Domino, diem festum celebrantes sub honore Mariae Virginis",
    "introitus_gaudeamus-sanctorum-omnium":
        "Gaudeamus omnes in Domino, diem festum celebrantes sub honore Sanctorum",
    "introitus_miserere-ad-te":
        "Miserere mihi, Domine, quoniam ad te clamavi tota die : quia",
    "offertoire_benedictus-es-et":
        "Benedictus es, Domine, doce me iustificationes tuas : et non tradas",
    "offertoire_ave-maria-et":
        "Ave Maria, gratia plena, Dominus tecum, benedicta tu in mulieribus",
    "offertoire_benedictus-es-domine":
        "Benedictus es, Domine, doce me iustificationes tuas : in labiis",
    "offertoire_improperium-expectavit-et":
        "Improperium exspectavit cor meum et miseriam, et sustinui qui simul",
}


def _sans_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normaliser(s: str) -> str:
    s = _sans_accents(s).lower()
    s = re.sub(r"[^a-z']+", " ", s)
    return " ".join(s.split())


def _slug(s: str, n: int = MOTS_COURT) -> str:
    return "-".join(_normaliser(s).split()[:n])


def _lignes_chantees(texte: str):
    """Lignes de texte utiles, en sautant rubriques et préfixes v./r./ps."""
    for ligne in texte.splitlines():
        s = ligne.strip()
        if not s or s[0] in "!&@*~#«»$":
            continue
        s = re.sub(r"^(v|r|ps|psalmus|gloria)\.\s*", "", s, flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            yield s


def incipit(texte: str, n: int = MOTS_COURT) -> str | None:
    if not texte or not texte.strip():
        return None
    mots: list[str] = []
    for s in _lignes_chantees(texte):
        mots.extend(s.split())
        if len(mots) >= n:
            break
    return " ".join(mots[:n]) if mots else None


def _est_doublon(nom: str) -> bool:
    return "doublon" in nom.lower()


def charger_mapping(chemin: Path) -> dict[str, str]:
    data = json.loads(chemin.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items()
            if not _est_doublon(k) and not _est_doublon(v)}


def indexer(mapping: dict[str, str], dossier: Path) -> list[dict]:
    """Une entrée par MP3 présent : préfixe, slug normalisé, chemin relatif."""
    if not dossier.is_dir():
        raise SystemExit(f"Dossier audio introuvable : {dossier.resolve()}")
    presents = {p.name: p for p in dossier.rglob("*.mp3")
                if not _est_doublon(p.name)}
    entrees: list[dict] = []
    for original, renomme in mapping.items():
        chemin = presents.get(renomme) or presents.get(original)
        if chemin is None:
            continue
        m = re.match(r"^([a-z]+)_(.+)\.mp3$", renomme)
        if m:
            prefixe, slug_norm = m.group(1), m.group(2)
        else:
            prefixe, slug_norm = "", renomme.removesuffix(".mp3")
        entrees.append({
            "cle": renomme.removesuffix(".mp3"),
            "prefixe": prefixe,
            "slug": _slug(slug_norm.replace("-", " "), n=MOTS_LONG),
            "chemin": chemin.relative_to(dossier).as_posix(),
        })
    return entrees


def _prefixes(partie: str) -> set[str]:
    return set(ALIAS.get(partie, [PARTIES[partie]]))


def trouver_mp3(partie: str, texte: str, inc_court: str | None,
                entrees: list[dict]) -> str | None:
    """1) incipit court sur le slug ; 2) repli 10 mots via INCIPITS_LONGS."""
    candidats = [e for e in entrees if e["prefixe"] in _prefixes(partie)]

    if inc_court:
        slug = _slug(inc_court)
        for e in candidats:
            if e["slug"] == slug or e["slug"].startswith(slug):
                return e["chemin"]

    long_texte = _normaliser(incipit(texte, MOTS_LONG) or "").split()
    if not long_texte:
        return None
    meilleur, score = None, 0
    for e in candidats:
        attendu = INCIPITS_LONGS.get(e["cle"])
        if not attendu:
            continue
        commun = 0
        for a, b in zip(long_texte, _normaliser(attendu).split()):
            if a != b:
                break
            commun += 1
        if commun > score:
            meilleur, score = e["chemin"], commun
    return meilleur if score >= SEUIL_LONG else None


def enrichir(messe: dict, entrees: list[dict]) -> dict:
    stats = {"trouves": 0, "manquants": 0}
    for langue in LANGUES:
        sections = messe.get("sections", {}).get(langue, {})
        for partie in PARTIES:
            bloc = sections.get(partie)
            if not isinstance(bloc, dict):
                continue
            texte = bloc.get("texte", "")
            inc = incipit(texte)
            mp3 = trouver_mp3(partie, texte, inc, entrees) if texte.strip() else None
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
    ap.add_argument("--audio", default="Graduale Project")
    ap.add_argument("--sortie", default="messes_audio.json")
    args = ap.parse_args(argv[1:])

    mapping = charger_mapping(Path(args.mapping))
    entrees = indexer(mapping, Path(args.audio))
    print(f"Entrées audio indexées (hors doublon) : {len(entrees)}")

    data = json.loads(Path(args.messes).read_text(encoding="utf-8"))
    total = {"trouves": 0, "manquants": 0}
    for i, messe in enumerate(data.get("messes", []), 1):
        s = enrichir(messe, entrees)
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
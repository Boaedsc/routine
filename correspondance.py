#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
correspondance.py — Construit correspondance.json : pour chaque fichier propre
(data/Latin/<Categ>/<Code>.txt) et chaque pièce chantée, donne l'incipit
(3 premiers mots) et le MP3 correspondant dans le dossier audio.

Les fichiers *_doublon*.mp3 sont ignorés.

Usage :
    python correspondance.py
    python correspondance.py --audio "Graduale Project" --data data --out correspondance.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DOSSIER_AUDIO_ATTENDU = "Graduale Project"

# pièce logique -> (préfixe MP3, clés possibles dans les fichiers data)
PIECES = {
    "introitus":  ("introitus",  ["Introitus"]),
    "graduel":    ("graduel",    ["Graduale", "GradualeP", "Alleluia", "Tractus"]),
    "trait":      ("trait",      ["Tractus"]),
    "alleluia":   ("alleluia",   ["Alleluia"]),
    "offertoire": ("offertoire", ["Offertorium"]),
    "communion":  ("communion",  ["Communio"]),
}

# Préfixes MP3 alternatifs (variantes de noms de fichiers)
PREFIXES_ALIAS = {"offertoire": ["offertoire", "offerorium"]}

SEPARATEURS = ("_", "：", ":")  # underscore, deux-points plein largeur, ASCII

# =====================================================================
# Normalisation (identique à messe.py)
# =====================================================================
def _strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def normaliser_incipit(texte: str) -> str:
    s = _strip_accents(texte).lower()
    s = re.sub(r"[^a-z']+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace(" ", "-")

def cle_audio(incipit: str) -> str:
    s = normaliser_incipit(incipit)
    if not s:
        return ""
    return "-".join(s.split("-")[:3])[:60]

# =====================================================================
# Parsing des fichiers data (identique à messe.py)
# =====================================================================
_RE_SECTION = re.compile(r"^\[(\w+)\]\s*$")

def lire_sections(chemin: Path) -> dict[str, str]:
    if not chemin.exists():
        return {}
    texte = chemin.read_text(encoding="utf-8", errors="replace")
    sections: dict[str, str] = {}
    courant, tampon = None, []
    for ligne in texte.splitlines():
        m = _RE_SECTION.match(ligne)
        if m:
            if courant is not None:
                sections[courant] = "\n".join(tampon).strip()
            courant, tampon = m.group(1), []
        elif courant is not None:
            tampon.append(ligne)
    if courant is not None:
        sections[courant] = "\n".join(tampon).strip()
    return sections

def _suivre_renvoi(ref: str) -> str | None:
    """'@Commune/C2a-1' -> 'Commune/C2a-1' (ou None)."""
    m = re.match(r"^@([\w\-]+)/([\w\-]+)\s*$", ref.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None

def bloc_resolu(section_valeur: str, data_latin: Path, cle: str) -> str:
    """Remplace les lignes @Categ/Code par le contenu de la section `cle` référencée."""
    nouvelles = []
    for ln in section_valeur.splitlines():
        if ln.lstrip().startswith("@"):
            base_ref = _suivre_renvoi(ln)
            if base_ref:
                ref_data = lire_sections(data_latin / f"{base_ref}.txt")
                if cle in ref_data:
                    nouvelles.append(ref_data[cle])
                    continue
        nouvelles.append(ln)
    return "\n".join(nouvelles).strip()

# =====================================================================
# Incipit (identique à messe.py, simplifié)
# =====================================================================
def premier_incipit(texte: str) -> str:
    out: list[str] = []
    for ligne in texte.splitlines():
        s = ligne.strip()
        if not s or s.startswith(("!", "&", "@", "*", "~", "#", "«", "»")):
            continue
        s = re.sub(r"^(v|r|ps|gloria|psalmus)\.\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"^[!*~#]+\s*", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if not s:
            continue
        out.append(s)
        if len(" ".join(out).split()) >= 3:
            break
    txt = " ".join(out).strip().rstrip(".,;:")
    return " ".join(txt.split()[:3])

# =====================================================================
# Index des MP3 (sans doublons)
# =====================================================================
def decouper_nom(stem: str) -> tuple[str, str] | None:
    for sep in SEPARATEURS:
        if sep in stem:
            prefixe, _, slug = stem.partition(sep)
            return prefixe.strip().lower(), cle_audio(slug)
    return None

def indexer_audio(audio_dir: Path) -> dict[str, dict[str, Path]]:
    idx: dict[str, dict[str, Path]] = {}
    if not audio_dir.is_dir():
        return idx
    for f in sorted(audio_dir.rglob("*.mp3")):
        if "doublon" in f.stem.lower():
            continue
        decoupe = decouper_nom(f.stem)
        if not decoupe:
            continue
        prefixe, slug = decoupe
        idx.setdefault(prefixe, {}).setdefault(slug, f)
    return idx

def trouver_mp3(idx: dict[str, dict[str, Path]], prefixe: str, incipit: str) -> Path | None:
    cle = cle_audio(incipit)
    slugs = idx.get(prefixe, {})
    if cle in slugs:
        return slugs[cle]
    for s, chemin in slugs.items():
        if s.startswith(cle) or cle.startswith(s):
            return chemin
    return None

# =====================================================================
# Construction
# =====================================================================
def construire(data_dir: Path, audio_dir: Path):
    data_latin = data_dir / "Latin"
    idx = indexer_audio(audio_dir)
    resultat: dict[str, dict[str, dict]] = {}
    manquants: list[str] = []

    for txt in sorted(data_latin.rglob("*.txt")):
        base = txt.stem
        sections = lire_sections(txt)
        entree: dict[str, dict] = {}

        for piece, (prefixe, cles_data) in PIECES.items():
            for cle_data in cles_data:
                if cle_data not in sections:
                    continue
                texte = bloc_resolu(sections[cle_data], data_latin, cle_data)
                incipit = premier_incipit(texte)
                if not incipit:
                    continue
                mp3 = None
                for p in PREFIXES_ALIAS.get(prefixe, [prefixe]):
                    mp3 = trouver_mp3(idx, p, incipit)
                    if mp3:
                        break
                entree[piece] = {
                    "incipit": incipit,
                    "cle": f"{prefixe}_{cle_audio(incipit)}",
                    "audio": mp3.as_posix() if mp3 else None,
                }
                if mp3 is None:
                    manquants.append(f"{base}\t{piece}\t{incipit}")
                break

        if entree:
            resultat[base] = entree

    return resultat, manquants, idx

# =====================================================================
# CLI
# =====================================================================
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Correspondance incipits / MP3")
    ap.add_argument("--audio", default=DOSSIER_AUDIO_ATTENDU)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="correspondance.json")
    args = ap.parse_args(argv[1:])

    data_dir, audio_dir = Path(args.data), Path(args.audio)
    if not (data_dir / "Latin").is_dir():
        print(f"Erreur : {data_dir / 'Latin'} introuvable.", file=sys.stderr)
        return 2

    print(f"Dossier audio attendu : {DOSSIER_AUDIO_ATTENDU}")
    print(f"Dossier audio utilisé : {audio_dir.resolve()}  (existe : {audio_dir.is_dir()})")
    if audio_dir.name != DOSSIER_AUDIO_ATTENDU:
        print(f"ATTENTION : le dossier utilisé ne s'appelle pas « {DOSSIER_AUDIO_ATTENDU} ».",
              file=sys.stderr)

    resultat, manquants, idx = construire(data_dir, audio_dir)
    nb_mp3 = sum(len(v) for v in idx.values())
    print(f"MP3 indexés (hors doublons) : {nb_mp3}")
    for pref, slugs in sorted(idx.items()):
        print(f"  {pref:<12} {len(slugs):>4}   ex. {sorted(slugs)[0]}")
    if nb_mp3 == 0:
        print("ATTENTION : aucun MP3 indexé. Vérifie le dossier audio et le format "
              "des noms (prefixe_slug.mp3).", file=sys.stderr)

    Path(args.out).write_text(
        json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("correspondance_manquants.txt").write_text("\n".join(manquants), encoding="utf-8")

    total = sum(len(v) for v in resultat.values())
    par_piece = Counter(l.split("\t")[1] for l in manquants)
    print(f"\n{len(resultat)} fichiers propres, {total} pièces chantées")
    print(f"  MP3 trouvés   : {total - len(manquants)}")
    print(f"  MP3 manquants : {len(manquants)}  {dict(par_piece)}")
    print(f"Écrit : {args.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
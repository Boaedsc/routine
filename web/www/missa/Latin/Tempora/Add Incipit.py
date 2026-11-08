#!/usr/bin/env python3
"""
officium_match.py
Pour chaque section (Introitus, Graduale, Tractus, Alleluia, Offertorium, Communio)
du fichier Officium, cherche l'entrée la plus proche dans gregobase.json
(distance de Levenshtein sur texte normalisé : sans accents, ponctuation ni espaces).
"""

import json
import re
import sys
import unicodedata

OFFICIUM_FILE = "web/www/missa/Latin/Tempora/Quad1-5.txt"
GREGOBASE_FILE = "gregobase.json"
SECTIONS = ["Introitus", "Graduale", "Tractus", "Alleluia", "Offertorium", "Communio"]


def strip_accents(text: str) -> str:
    text = text.replace("æ", "ae").replace("Æ", "AE")
    text = text.replace("œ", "oe").replace("Œ", "OE")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Sans accents, sans ponctuation, sans espaces, en minuscules."""
    text = strip_accents(text).lower()
    return re.sub(r"[^a-z]", "", text)


def levenshtein(a: str, b: str) -> int:
    """Distance de Levenshtein, implémentation O(n*m) en mémoire O(min)."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def parse_officium(path: str) -> dict:
    """
    Retourne {section: texte} en ne gardant que la première occurrence de chaque section.
    Les lignes de type '!Ps 24:17' ou '&Gloria' ou 'v.' sont conservées dans le texte
    mais le nettoyage (normalize) ne garde que les lettres.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    sections, current, buf = {}, None, []
    header = re.compile(r"^\[([^\]]+)\]\s*$")

    for line in lines:
        m = header.match(line.strip())
        if m:
            if current and current not in sections:
                sections[current] = "\n".join(buf)
            current = m.group(1).strip()
            buf = []
        elif current:
            buf.append(line)
    if current and current not in sections:
        sections[current] = "\n".join(buf)

    return sections


def extract_chant_text(raw: str) -> str:
    """Retire les références (!Ps 24:17), les rubriques (&Gloria, $Per Dominum) et les
    marqueurs (v., V.) ; garde le texte chanté."""
    kept = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] in "!&$@" or s.startswith("(") or s == "_":
            continue
        s = re.sub(r"^[vV]\.\s*", "", s)
        kept.append(s)
    return " ".join(kept)


def load_gregobase(path: str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # format : [incipit, version, texte_normalise]
    return data


def best_match(query_norm: str, db):
    best = None
    for incipit, version, texte in db:
        d = levenshtein(query_norm, texte)
        if best is None or d < best[0]:
            best = (d, incipit, version, texte)
    return best


def main():
    sections = parse_officium(OFFICIUM_FILE)
    db = load_gregobase(GREGOBASE_FILE)
    print(f"{len(db)} entrées chargées depuis {GREGOBASE_FILE}\n")

    for name in SECTIONS:
        if name not in sections:
            print(f"[{name}] : section absente")
            continue
        chant = extract_chant_text(sections[name])
        query = normalize(chant)
        if not query:
            print(f"[{name}] : texte vide après nettoyage")
            continue

        d, incipit, version, texte = best_match(query, db)
        similarity = 1 - d / max(len(query), len(texte), 1)
        print(f"[{name}]")
        print(f"  requête   : {query[:80]}{'...' if len(query) > 80 else ''}")
        print(f"  incipit   : {incipit}")
        print(f"  version   : {version}")
        print(f"  distance  : {d} ({similarity:.1%} de similarité)\n")


if __name__ == "__main__":
    main()
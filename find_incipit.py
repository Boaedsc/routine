#!/usr/bin/env python3
"""
find_incipit.py
Identifie les incipits Introitus / Graduale / Tractus / Alleluia / Offertorium / Communio
à partir du texte latin d'une messe et les compare au dump SQL Gregobase.

Utilisable :
- comme module : incipits_pour_messe(sections_latines, db) -> dict
- en ligne de commande : python find_incipit.py [fichier_officium] [gregobase_online.sql]
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional
from collections import Counter

GREGOBASE_FILE = "gregobase_online.sql"
OFFICIUM_FILE = "web/www/missa/Latin/Tempora/Quad1-5.txt"

PREFIX_LEN = 40
TOP_K = 20
NGRAM_SIZE = 3

# Code de type Gregobase (colonne office-part) pour chaque type de chant
PART_CODES = {
    "Introitus": "in",
    "Graduale": "gr",
    "Tractus": "tr",
    "Alleluia": "al",
    "Offertorium": "of",
    "Communio": "co",
}

ALLELUIA_RE = re.compile(r"Allel[úu]ja", re.IGNORECASE)
SEPARATEUR_TRACTUS_RE = re.compile(r"^!\s*Tractus\s*$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Normalisation et parsing
# ---------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    text = text.replace("æ", "ae").replace("Æ", "AE")
    text = text.replace("œ", "oe").replace("Œ", "OE")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Normalise le latin pour comparer les incipits (u/v et i/j confondus)."""
    text = strip_accents(text).lower().replace("v", "u").replace("j", "i")
    return re.sub(r"[^a-z]", "", text)


def textualiser_gabc(gabc: str) -> str:
    """Extrait les syllabes chantées du GABC en retirant sa notation.

    Les syllabes sont déjà découpées dans le GABC : AL(dc~)le(c/e'gF)lú(dc){ia}.
    Retirer les parenthèses (neumes) SANS les remplacer par une espace recolle
    les syllabes d'un même mot ; seuls les espaces réels du GABC séparent les
    mots. Cela n'a de toute façon pas d'effet sur normalize(), qui supprime
    tout sauf les lettres.
    """
    if not isinstance(gabc, str):
        return ""
    body = gabc.split("%%", 1)[1] if "%%" in gabc else gabc
    # Dans les GABC sans séparateur d'en-tête, la première clef marque le début.
    body = re.sub(r"^.*?\([cf][0-9]+\)", "", body, count=1, flags=re.S)
    body = re.sub(r"\([^)]*\)", "", body)      # neumes/indications
    body = re.sub(r"<[^>]*>", "", body)        # balises de formatage (<i>, <sp>, <eu>...)
    body = body.replace("{", "").replace("}", "")  # conserver le texte entre accolades
    body = re.sub(r"\[[^]]*\]", "", body)
    return body


def _split_sql_statements(sql: str):
    """Découpe les instructions SQL sans confondre les ; contenus dans les chaînes."""
    start = 0
    i = 0
    quote = None
    while i < len(sql):
        c = sql[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    i += 2
                    continue
                quote = None
        elif c in ("'", '"', "`"):
            quote = c
        elif c == ";":
            yield sql[start:i]
            start = i + 1
        i += 1
    if sql[start:].strip():
        yield sql[start:]


def _parse_sql_string(s: str, pos: int):
    quote = s[pos]
    pos += 1
    out = []
    escapes = {"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a"}
    while pos < len(s):
        c = s[pos]
        if c == "\\":
            pos += 1
            if pos >= len(s):
                out.append("\\")
                break
            nxt = s[pos]
            out.append(escapes.get(nxt, nxt))
            pos += 1
        elif c == quote:
            if pos + 1 < len(s) and s[pos + 1] == quote:
                out.append(quote)
                pos += 2
            else:
                return "".join(out), pos + 1
        else:
            out.append(c)
            pos += 1
    raise ValueError("chaîne SQL non terminée")


def _parse_sql_tuple(s: str, pos: int):
    """Lit un tuple VALUES de scalaires SQL, avec les chaînes décodées."""
    if pos >= len(s) or s[pos] != "(":
        raise ValueError("tuple SQL attendu")
    pos += 1
    values = []
    while True:
        while pos < len(s) and s[pos].isspace():
            pos += 1
        if pos >= len(s):
            raise ValueError("tuple SQL incomplet")
        if s[pos] == ")":
            return values, pos + 1
        if s[pos] in ("'", '"'):
            value, pos = _parse_sql_string(s, pos)
        else:
            begin = pos
            depth = 0
            while pos < len(s):
                c = s[pos]
                if c == "(":
                    depth += 1
                elif c == ")":
                    if depth == 0:
                        break
                    depth -= 1
                elif c == "," and depth == 0:
                    break
                pos += 1
            token = s[begin:pos].strip()
            if not token:
                raise ValueError("valeur SQL vide")
            if token.upper() == "NULL":
                value = None
            elif re.fullmatch(r"[+-]?\d+", token):
                value = int(token)
            elif re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?", token):
                value = float(token)
            else:
                value = token
        values.append(value)
        while pos < len(s) and s[pos].isspace():
            pos += 1
        if pos < len(s) and s[pos] == ",":
            pos += 1
            continue
        if pos < len(s) and s[pos] == ")":
            return values, pos + 1
        raise ValueError("séparateur de valeur SQL attendu")


def _parse_insert_chants(statement: str):
    """Retourne colonnes et tuples d'un INSERT ciblant gregobase_chants."""
    # Les dumps MySQL placent souvent des commentaires entre les instructions.
    statement = re.sub(r"\A(?:\s+|--[^\n]*(?:\n|$)|#[^\n]*(?:\n|$)|/\*.*?\*/)*", "", statement, flags=re.S)
    head = re.match(r"\s*INSERT\s+INTO\s+`?([\w$]+)`?\s*", statement, re.I)
    if not head or head.group(1).lower() != "gregobase_chants":
        return []
    pos = head.end()
    while pos < len(statement) and statement[pos].isspace():
        pos += 1
    if pos >= len(statement) or statement[pos] != "(":
        return []
    pos += 1
    columns = []
    while pos < len(statement):
        while pos < len(statement) and (statement[pos].isspace() or statement[pos] == ","):
            pos += 1
        if statement[pos] == ")":
            pos += 1
            break
        if statement[pos] == "`":
            end = statement.find("`", pos + 1)
            if end < 0:
                return []
            columns.append(statement[pos + 1:end])
            pos = end + 1
        else:
            m = re.match(r"[\w$-]+", statement[pos:])
            if not m:
                return []
            columns.append(m.group(0))
            pos += len(m.group(0))
    m = re.search(r"\bVALUES\b", statement[pos:], re.I)
    if not m:
        return []
    pos += m.end()
    rows = []
    while pos < len(statement):
        while pos < len(statement) and (statement[pos].isspace() or statement[pos] == ","):
            pos += 1
        if pos >= len(statement):
            break
        if statement[pos] != "(":
            break
        vals, pos = _parse_sql_tuple(statement, pos)
        if len(vals) != len(columns):
            raise ValueError("nombre de valeurs différent des colonnes dans gregobase_chants")
        rows.append(dict(zip(columns, vals)))
    return rows


def read_gregobase_sql(path: str = GREGOBASE_FILE) -> list:
    """Lit les lignes gregobase_chants d'un dump SQL sans serveur."""
    fichier = Path(path)
    if not path or not fichier.is_file():
        return []
    sql = fichier.read_text(encoding="utf-8", errors="replace")
    rows = []
    for statement in _split_sql_statements(sql):
        rows.extend(_parse_insert_chants(statement))
    return rows


def decode_gabc(value):
    """Décode la colonne gabc (JSON [["tex",...],["gabc","..."]]) en notation GABC.

    Si la valeur n'est pas ce JSON, elle est conservée telle quelle.
    """
    if not isinstance(value, str) or not value:
        return ""
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
    if isinstance(parsed, list):
        for entry in parsed:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2 and str(entry[0]).lower() == "gabc":
                return entry[1] if isinstance(entry[1], str) else ""
    return value


def parse_officium(path: str) -> dict:
    """Retourne {nom_section: texte_brut} en ne gardant que la première occurrence."""
    sections = {}
    current = None
    buffer = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\[(\w+)\]\s*$", line.strip())
            if m:
                if current and current not in sections:
                    sections[current] = "\n".join(buffer)
                current = m.group(1)
                buffer = []
            elif current:
                buffer.append(line.rstrip("\n"))
    if current and current not in sections:
        sections[current] = "\n".join(buffer)
    return sections


def clean_lines(section: str) -> list:
    """
    Garde les lignes de texte chanté.
    Retire : références (!...), rubriques (&..., @..., $...), séparateurs (_),
    rubriques entre parenthèses, marqueurs de verset (v./V.).
    """
    out = []
    for line in section.splitlines():
        line = line.strip()
        if (not line or line.startswith("!") or line.startswith("&")
                or line.startswith("@") or line.startswith("$") or line == "_"):
            continue
        line = re.sub(r"\(.*?\)", "", line)
        line = re.sub(r"^[vV]\.\s*", "", line)
        if line:
            out.append(line)
    return out


def _bloc_vers_chants(texte: str, type_bloc: str, source: str) -> list:
    """
    À partir du texte d'un bloc, sépare la partie chant (type_bloc) de la partie
    alléluia éventuelle. Retourne une liste de chants.
    """
    chants = []
    if not ALLELUIA_RE.search(texte):
        if texte.strip():
            chants.append({"type": type_bloc, "source": source, "texte": texte.strip()})
        return chants

    parts = ALLELUIA_RE.split(texte, maxsplit=1)
    avant = parts[0].strip()
    apres = parts[1].strip() if len(parts) > 1 else ""

    if avant:
        chants.append({"type": type_bloc, "source": source, "texte": avant})
    chants.append({"type": "Alleluia", "source": source,
                   "texte": "Allelúja " + apres})
    return chants


def extract_chants(sections: dict) -> list:
    """
    Extrait tous les chants de la messe à partir des sections Officium.

    Règles :
    - [Tractus] : chant de type Tractus.
    - [Alleluia] : chant de type Alleluia.
    - [GradualeP] : alléluia du temps pascal, traité comme Alleluia.
    - [Graduale] :
        * les blocs séparés par "_" suivis de "!Tractus" sont des Tractus ;
        * les blocs contenant "Allelúja" sont coupés : la partie avant est un
          Graduale (ou Tractus), la partie après est un Alleluia ;
        * les autres blocs sont des Graduale.
    """
    chants = []

    if "Tractus" in sections:
        texte = " ".join(clean_lines(sections["Tractus"]))
        if texte:
            chants.append({"type": "Tractus", "source": "Tractus", "texte": texte})

    if "Alleluia" in sections:
        texte = " ".join(clean_lines(sections["Alleluia"]))
        if texte:
            chants.append({"type": "Alleluia", "source": "Alleluia", "texte": texte})

    if "GradualeP" in sections:
        texte = " ".join(clean_lines(sections["GradualeP"]))
        if texte:
            chants.append({"type": "Alleluia", "source": "GradualeP", "texte": texte})

    if "Graduale" in sections:
        # Découpe en blocs : séparateur "_" ou changement de section "!Tractus"
        blocs = []     # liste de (type, lignes)
        courant = []
        type_courant = "Graduale"
        for raw in sections["Graduale"].splitlines():
            stripped = raw.strip()
            if stripped == "_":
                if courant:
                    blocs.append((type_courant, courant))
                courant = []
                type_courant = "Graduale"
                continue
            if SEPARATEUR_TRACTUS_RE.match(stripped):
                if courant:
                    blocs.append((type_courant, courant))
                courant = []
                type_courant = "Tractus"
                continue
            courant.append(raw)
        if courant:
            blocs.append((type_courant, courant))

        for idx, (type_bloc, lignes) in enumerate(blocs):
            texte = " ".join(clean_lines("\n".join(lignes)))
            if not texte:
                continue
            chants.extend(_bloc_vers_chants(texte, type_bloc, f"Graduale[{idx}]"))

    return chants


# ---------------------------------------------------------------------------
# Comparaison
# ---------------------------------------------------------------------------

def ngrams(text: str, n: int = NGRAM_SIZE) -> Counter:
    if len(text) < n:
        return Counter([text]) if text else Counter()
    return Counter(text[i:i + n] for i in range(len(text) - n + 1))


def dice(c1: Counter, c2: Counter) -> float:
    inter = sum((c1 & c2).values())
    total = sum(c1.values()) + sum(c2.values())
    return 2 * inter / total if total else 0.0


def levenshtein(a: str, b: str) -> int:
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


def load_gregobase(path: str = GREGOBASE_FILE) -> list:
    """Charge le dump SQL et prépare les entrées compatibles avec le matching."""
    rows = read_gregobase_sql(path)
    entries = []
    lignes_avec_gabc = 0
    for row in rows:
        gabc = decode_gabc(row.get("gabc"))
        if gabc:
            lignes_avec_gabc += 1
        part = row.get("office-part") or ""
        if row.get("duplicateof") is not None:
            continue
        gabc_prefix = normalize(textualiser_gabc(gabc))[:PREFIX_LEN]
        incipit = row.get("incipit") or ""
        prefix = gabc_prefix or normalize(str(incipit))[:PREFIX_LEN]
        if not prefix:
            continue
        entry = {
            "id": row.get("id"), "incipit": str(incipit),
            "version": str(row.get("version") or ""), "part": str(part),
            "prefix": prefix, "grams": ngrams(prefix),
        }
        if gabc:
            entry["gabc"] = gabc
        entries.append(entry)
    if not rows:
        print("Diagnostic Gregobase : aucune ligne gregobase_chants lue dans {!r} "
              "(fichier absent, vide, ou pas de INSERT INTO gregobase_chants)."
              .format(path), file=sys.stderr)
    elif not lignes_avec_gabc:
        print("Diagnostic Gregobase : aucun GABC non vide détecté dans gregobase_chants.",
              file=sys.stderr)
    return entries


def _requete_match(texte: str) -> str:
    """Écarte le refrain répété « Alleluia » avant de comparer le verset."""
    texte = re.sub(r"^[\W_]*(?:Allel[úu]ja[\s,.;:!?]*)+", "",
                   texte.strip(), flags=re.IGNORECASE)
    return normalize(" ".join(clean_lines(texte)))[:PREFIX_LEN]


def best_match(query_prefix: str, db: list, part: Optional[str] = None):
    pool = [e for e in db if part is None or e["part"] == part]
    if not pool:
        return None
    query_prefix = normalize(query_prefix)[:PREFIX_LEN]
    if not query_prefix:
        return None
    query_grams = ngrams(query_prefix)
    scored = [(dice(query_grams, e["grams"]), e) for e in pool]
    scored.sort(key=lambda x: x[0], reverse=True)

    best = None
    for dice_score, e in scored[:TOP_K]:
        d = levenshtein(query_prefix, e["prefix"])
        sim = 1 - d / max(len(query_prefix), len(e["prefix"]), 1)
        if best is None or sim > best["sim"]:
            best = {
                "incipit": e["incipit"],
                "version": e["version"],
                "prefix": e["prefix"],
                "dice": dice_score,
                "lev": d,
                "distance": d,
                "sim": sim,
                **({"gabc": e["gabc"]} if e.get("gabc") else {}),
            }
    return best


# ---------------------------------------------------------------------------
# API pour la génération de messes
# ---------------------------------------------------------------------------

def _texte_section(valeur) -> str:
    if isinstance(valeur, dict):
        valeur = valeur.get("texte", "")
    return valeur or ""


def _formater(m: Optional[dict], source: str) -> dict:
    if m is None:
        return {"incipit": None, "version": None, "source": source,
                "similarite": 0.0, "distance": None}
    resultat = {
        "incipit": m["incipit"],
        "version": m["version"],
        "source": source,
        "similarite": round(m["sim"], 3),
        "distance": m.get("distance", m.get("lev")),
    }
    if m.get("gabc"):
        resultat["gabc"] = m["gabc"]
    return resultat


def _debut_chant(texte: str) -> str:
    """Texte chantable d'une section, brute (Officium) ou déjà nettoyée.

    clean_lines retire références (!...), rubriques (&, @, $), séparateurs (_),
    parenthèses et préfixe 'v.'/'V.'.
    """
    return " ".join(clean_lines(texte or "")).strip()


def preparer_chants(sections: dict) -> list:
    """Transforme des sections (brutes OU {fichier, section, texte}) en chants.

    Format de sortie, identique quelle que soit l'entrée :
        [{"type": "Introitus", "cle": "Introitus", "texte": "..."}, ...]

    - Introitus / Offertorium / Communio : un chant chacun.
    - Graduale contenant "_", "!Tractus" ou "Allelúja" : décomposé via
      extract_chants en Graduale / Tractus / Alleluia.
    - Tractus et Alleluia fournis explicitement : un chant chacun, sauf s'ils
      ont déjà été produits par la décomposition du Graduale.
    - Les chants vides sont ignorés.
    """
    bruts = {k: _texte_section(v) for k, v in sections.items()}
    chants = []

    for nom in ("Introitus", "Offertorium", "Communio"):
        texte = _debut_chant(bruts.get(nom, ""))
        if texte:
            chants.append({"type": nom, "cle": nom, "texte": texte})

    grad = bruts.get("Graduale", "")
    composite = bool(grad) and (
        ALLELUIA_RE.search(grad)
        or re.search(r"^\s*_\s*$", grad, re.M)
        or re.search(r"^\s*!\s*Tractus\s*$", grad, re.M | re.I)
    )
    if composite:
        for c in extract_chants({"Graduale": grad}):
            cle = c["type"]
            if any(x["cle"] == cle for x in chants):
                cle = f"{c['type']}:{c['source']}"
            chants.append({"type": c["type"], "cle": cle, "texte": c["texte"]})
    elif _debut_chant(grad):
        chants.append({"type": "Graduale", "cle": "Graduale",
                       "texte": _debut_chant(grad)})

    for nom in ("Tractus", "Alleluia"):
        texte = _debut_chant(bruts.get(nom, ""))
        if not texte:
            continue
        if any(c["type"] == nom for c in chants):
            continue
        chants.append({"type": nom, "cle": nom, "texte": texte})

    return chants


def incipits_pour_messe(sections_latines: dict, db: list) -> dict:
    """Calcule les incipits d'une messe, quel que soit le format d'entrée.

    Retourne un dict {cle: info} avec cle = "Introitus", "Graduale",
    "Tractus", "Alleluia", "Offertorium", "Communio" (ou "Type:source"
    si plusieurs chants du même type existent).
    """
    resultats = {}
    for chant in preparer_chants(sections_latines):
        if chant["type"] == "Alleluia":
            query = _requete_match(chant["texte"])
        else:
            query = normalize(chant["texte"])[:PREFIX_LEN]
        if not query:
            continue
        m = best_match(query, db, PART_CODES[chant["type"]])
        resultats[chant["cle"]] = _formater(m, source=chant["cle"])
    return resultats


# ---------------------------------------------------------------------------
# Ligne de commande (test sur un fichier Officium)
# ---------------------------------------------------------------------------

def main():
    chemin = sys.argv[1] if len(sys.argv) > 1 else OFFICIUM_FILE
    sql_path = sys.argv[2] if len(sys.argv) > 2 else GREGOBASE_FILE
    sections = parse_officium(chemin)
    db = load_gregobase(sql_path)
    print(f"{len(db)} entrées chargées depuis {sql_path}\n")
    for cle, r in incipits_pour_messe(sections, db).items():
        print(f"[{cle}] {r['incipit']} ({r['version']}, {r['similarite']:.1%}, {r['source']})")


if __name__ == "__main__":
    main()
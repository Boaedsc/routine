#!/usr/bin/env python3
"""Usage : generer_messe.py [options] --gregobase gregobase_online.sql

Prégénère messes/AAAA-MM-JJ.json, enrichit les sections chantées à partir
de Gregobase (dump SQL ou JSON), puis génère les PDF de partition associés.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from typing import Optional
from pathlib import Path

import audio_messe
from messe import main_mass
from find_incipit import (PART_CODES, incipits_pour_messe, load_gregobase,
                          extract_chants, clean_lines, ALLELUIA_RE)
from gabc_engine import rendre_gabc, GregorioIntrouvable


def plage(debut: dt.date, fin: dt.date):
    d = debut
    while d <= fin:
        yield d
        d += dt.timedelta(days=1)


def _match_section(partie: str, correspondances: dict) -> Optional[dict]:
    """Choisit le match Gregobase propre à la partie, sinon son premier chant extrait."""
    if partie in correspondances:
        return correspondances[partie]
    prefix = partie + ":"
    return next((info for cle, info in correspondances.items() if cle.startswith(prefix)), None)


def ajouter_incipits(messe: dict, db: list, audio_idx: Optional[dict] = None) -> None:
    """Ajoute incipit (avec version/distance), GABC puis MP3 aux sections latines.

    Les autres propriétés de chaque section sont conservées après les champs
    d'enrichissement. Les textes non chantés ou sans correspondance restent intacts.
    """
    langues = messe.get("sections", {})
    sections = langues.get("Latin", {}) if isinstance(langues, dict) else {}
    if not isinstance(sections, dict) or not sections:
        return

    # Certains fichiers source rangent le verset alléluia à la suite du
    # Graduale, alors que la structure JSON expose deux pièces distinctes.
    # On sépare pour l'affichage du JSON, mais on garde le texte complet
    # d'origine pour le matching (preparer_chants refait la décomposition).
    graduale = sections.get("Graduale")
    alleluia = sections.get("Alleluia")
    grad_text = graduale.get("texte", "") if isinstance(graduale, dict) else ""
    all_text = alleluia.get("texte", "") if isinstance(alleluia, dict) else ""
    texte_graduale_complet = grad_text
    if grad_text and ALLELUIA_RE.search(grad_text):
        chants = extract_chants({"Graduale": grad_text})
        grad_chant = next((c for c in chants if c["type"] == "Graduale"), None)
        all_chant = next((c for c in chants if c["type"] == "Alleluia"), None)
        if grad_chant:
            graduale["texte"] = " ".join(clean_lines(grad_chant["texte"]))
        if all_chant:
            verset = re.sub(r"^[\W_]*(?:Allel[úu]ja[\s,.;:!?]*)+", "",
                            all_chant["texte"].strip(), flags=re.IGNORECASE)
            if not all_text or ALLELUIA_RE.match(all_text.strip()):
                alleluia["texte"] = " ".join(clean_lines(verset))

    # Matching : incipits_pour_messe se charge du pré-traitement
    # (preparer_chants). On lui donne les sections latines avec le
    # Graduale d'origine (avant séparation Graduale/Alleluia).
    entree = {nom: bloc for nom, bloc in sections.items() if isinstance(bloc, dict)}
    if isinstance(graduale, dict):
        entree["Graduale"] = {**graduale, "texte": texte_graduale_complet}
    correspondances = incipits_pour_messe(entree, db)

    for partie in PART_CODES:
        bloc = sections.get(partie)
        if not isinstance(bloc, dict):
            continue
        if not bloc.get("texte"):
            continue
        info = _match_section(partie, correspondances) or {}

        # L'incipit est celui de l'entrée Gregobase gagnante, jamais dérivé
        # du texte de la messe. Garder l'ordre contractuel des clés.
        incipit_info = {
            "incipit": info.get("incipit"),
            "version": info.get("version"),
            "distance": info.get("distance"),
            "similarite": info.get("similarite"),
            "source": info.get("source", partie),
        }
        enrichi = {"texte": bloc.get("texte"), "incipit": incipit_info,
                   "gabc": info.get("gabc"), "mp3": None}

        enrichi.update((k, v) for k, v in bloc.items()
                       if k not in ("texte", "incipit", "gabc", "mp3"))
        sections[partie] = enrichi

    # Enrichir uniquement Latin; audio_messe lit incipit (string ou objet)
    # et le type de chant, puis place mp3 après gabc.
    audio_messe.enrichir(messe, audio_idx or {})


def slugifier(texte: str) -> str:
    """Transforme un texte en nom de fichier sûr : minuscules, sans accents ni espaces."""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    texte = re.sub(r"[^\w]+", "-", texte.lower()).strip("-")
    return texte or "sans-nom"


def generer_partitions(messe: dict, dossier_partitions: Path, forcer: bool = False) -> int:
    """Génère un PDF par section latine disposant d'un GABC. Retourne le nombre produit."""
    sections = messe.get("sections", {}).get("Latin", {})
    if not isinstance(sections, dict):
        return 0
    produits = 0
    for partie, bloc in sections.items():
        if not isinstance(bloc, dict):
            continue
        gabc = bloc.get("gabc")
        if not gabc:
            continue
        incipit = (bloc.get("incipit") or {}).get("incipit") or partie
        nom = f"{slugifier(partie)}_{slugifier(incipit)}"
        cible = dossier_partitions / f"{nom}.pdf"
        if cible.exists() and not forcer:
            continue
        try:
            rendre_gabc(gabc, nom=nom, dossier=dossier_partitions, png=False)
            produits += 1
        except (ValueError, GregorioIntrouvable, RuntimeError) as e:
            print(f"Partition ignorée {nom} : {e}", file=sys.stderr)
    return produits


def diagnostic_gregobase(path: str, nombre: int = 3) -> None:
    """Résume les chants et quelques exemples de la source Gregobase."""
    fichier = Path(path)
    if not fichier.is_file():
        print("Diagnostic Gregobase : fichier introuvable : {}".format(path))
        return
    from find_incipit import read_gregobase_sql, read_gregobase_json, decode_gabc
    if str(path).lower().endswith(".json"):
        rows = read_gregobase_json(path)
    else:
        rows = read_gregobase_sql(path)
    repartition = {}
    avec_gabc = 0
    for row in rows:
        part = row.get("office-part") or "(NULL)"
        repartition[part] = repartition.get(part, 0) + 1
        if decode_gabc(row.get("gabc")):
            avec_gabc += 1
    print("Lignes lues de gregobase_chants : {}".format(len(rows)))
    print("Répartition par office-part : {}".format(
        ", ".join("{}={}".format(k, repartition[k]) for k in sorted(repartition)) or "(aucune)"))
    print("Lignes avec gabc non vide : {}".format(avec_gabc))
    for row in rows[:nombre]:
        gabc = decode_gabc(row.get("gabc"))
        preview = (gabc or "").replace("\n", " ").replace("\r", " ")[:80]
        print("Exemple id={!r}, incipit={!r}, version={!r}, part={!r}, gabc={!r}".format(
            row.get("id"), row.get("incipit"), row.get("version"), row.get("office-part"), preview))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--debut", type=dt.date.fromisoformat, default=dt.date(2026, 1, 1))
    ap.add_argument("--fin", type=dt.date.fromisoformat, default=dt.date(2028, 12, 31))
    ap.add_argument("--racine", default=".", help="racine du dépôt")
    ap.add_argument("--dossier", default="messes")
    ap.add_argument("--mapping", default="mapping_renommage.json")
    ap.add_argument("--audio", default="Graduale Project")
    ap.add_argument("--gregobase", default="gregobase_online.sql",
                    help="chemin du dump SQL (ou export .json) de Gregobase")
    ap.add_argument("--partitions", default="partitions",
                    help="dossier de sortie des PDF de partition")
    ap.add_argument("--sans-partitions", action="store_true",
                    help="ne pas générer les PDF de partition")
    ap.add_argument("--diag-gregobase", action="store_true",
                    help="diagnostiquer la source Gregobase et quitter")
    ap.add_argument("--forcer", action="store_true", help="réécrire les fichiers existants")
    args = ap.parse_args(argv[1:])

    if args.diag_gregobase:
        diagnostic_gregobase(args.gregobase)
        return 0

    racine = Path(args.racine).expanduser().resolve()
    dossier = Path(args.dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    dossier_partitions = Path(args.partitions)
    if not args.sans_partitions:
        dossier_partitions.mkdir(parents=True, exist_ok=True)

    db = load_gregobase(args.gregobase)
    print(f"Gregobase : {len(db)} entrées chargées depuis {args.gregobase}", file=sys.stderr)
    if not db:
        print("ATTENTION : base Gregobase vide, aucun incipit ne sera trouvé.", file=sys.stderr)

    audio_idx = None
    mapping_path, audio_path = Path(args.mapping), Path(args.audio)
    if mapping_path.is_file() and audio_path.is_dir():
        audio_idx = audio_messe.indexer(audio_messe.charger_mapping(mapping_path), audio_path)

    ecrits = sautes = erreurs = partitions = 0
    for d in plage(args.debut, args.fin):
        cible = dossier / f"{d.isoformat()}.json"
        if cible.exists() and not args.forcer:
            sautes += 1
            continue
        try:
            data = main_mass(d, racine)
            for messe in data.get("messes", []):
                ajouter_incipits(messe, db, audio_idx)
                if not args.sans_partitions:
                    partitions += generer_partitions(messe, dossier_partitions,
                                                     forcer=args.forcer)
            cible.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            ecrits += 1
        except Exception as e:
            erreurs += 1
            print(f"ERREUR {d}: {e}", file=sys.stderr)

    print(f"Écrits : {ecrits} | Sautés : {sautes} | Erreurs : {erreurs} | "
          f"Partitions : {partitions}")
    return 0 if erreurs == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
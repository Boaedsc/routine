#!/usr/bin/env python3
"""
messe.py — Génère le contenu de la messe pour une date donnée.

Comportement :
  * Latin puis français pour la plupart des sections.
  * Lecture et Évangile : français seul.
  * Pour chaque section « audio » (Introitus, Graduale,
    Alleluia/Tractus, Offertorium, Communio), on charge
    `correspondance.json` (dans le même dossier que ce fichier)
    et on y ajoute le champ `audios` issu de l'entrée correspondante.

Si aucune entrée n'est trouvée ou si le champ `audio` est null,
le champ `audios` reste à None : le lecteur s'affichera sans MP3,
sans qu'aucune exception ne soit levée.

Les JSON sont écrits dans le dossier `messes/` (un fichier par jour,
nommé AAAA-MM-JJ.json), à côté de ce script.

Usage :
    python messe.py 2026-10-24            # affiche le JSON d'une date
    python messe.py 2026-10-24 --ecrire   # écrit messes/2026-10-24.json
    python messe.py annee 2026            # écrit un JSON par jour de 2026
    python messe.py test                  # lance les tests de non-régression
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from calendrier import fichiers_du_jour, celebration

# ── Chemins ─────────────────────────────────────────────────────────────────
# Ce fichier, calendrier.py et correspondance.json vivent dans le même
# dossier ; data/ est juste à côté.
RACINE = Path(__file__).resolve().parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_SORTIE = RACINE / "messes"
FICHIER_CORRESPONDANCE = RACINE / "correspondance.json"

# ── Plan de la messe ────────────────────────────────────────────────────────
# (clé de section dans le format Divinum Officium,
#  titre affiché,
#  langues à concaténer dans l'ordre)
PLAN = [
    ("Introitus",     "Introït",       ["Latin", "Francais"]),
    ("Lectio",        "Lecture",       ["Francais"]),
    ("Graduale",      "Graduel",       ["Latin", "Francais"]),
    ("Alleluia",      "Alléluia",      ["Latin", "Francais"]),
    ("Evangelium",    "Évangile",      ["Francais"]),
    ("Offertorium",   "Offertoire",    ["Latin", "Francais"]),
    ("Communio",      "Communion",     ["Latin", "Francais"]),
]

# ── Mapping Divinum Officium → champ dans correspondance.json ───────────────
# Pour « Alleluia / Tractus », le fichier source peut s'appeler
# `[Alleluia]` ou `[Tractus]` ; on essaie d'abord `alleluia`, puis
# `trait` en repli.
MAPPING_AUDIO = {
    "Introitus":   ("introitus",),
    "Graduale":    ("graduel",),
    "Alleluia":    ("alleluia", "trait"),
    "Offertorium": ("offertoire",),
    "Communio":    ("communion",),
}

# ── Chargement de la correspondance audio ──────────────────────────────────
def charger_correspondance(chemin: Path) -> dict:
    """
    Charge correspondance.json. Retourne un dict vide (et n'échoue
    jamais) si le fichier est absent, vide ou corrompu.
    """
    if not chemin.exists():
        return {}
    try:
        with chemin.open("r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return donnees if isinstance(donnees, dict) else {}

# ── Lecture des fichiers Divinum Officium ──────────────────────────────────
def lire_sections(chemin: Path) -> dict:
    """
    Renvoie {nom_section: contenu} pour un fichier Divinum Officium
    (sections délimitées par des lignes `[Nom]`).
    """
    sections = {}
    if not chemin.exists():
        return sections
    texte = chemin.read_text(encoding="utf-8")
    courant, tampon = None, []
    for ligne in texte.splitlines():
        m = re.match(r"^\[(\w+)\]\s*$", ligne)
        if m:
            if courant is not None:
                sections[courant] = "\n".join(tampon).strip()
            courant, tampon = m.group(1), []
        elif courant is not None:
            tampon.append(ligne)
    if courant is not None:
        sections[courant] = "\n".join(tampon).strip()
    return sections

def propre_du_jour(d: date, langue: str, fichiers: list) -> dict:
    """Concatène les sections des fichiers du jour pour une langue."""
    propre = {}
    dossier_langue = DOSSIER_DATA / langue
    for f in fichiers:
        chemin = dossier_langue / f"{f}.txt"
        for k, v in lire_sections(chemin).items():
            propre.setdefault(k, v)
    return propre

# ── Résolution de la clé du jour ───────────────────────────────────────────
def cle_jour(fichier: str) -> str:
    """
    Extrait la clé de correspondance d'un nom de fichier calendrier.

    Le calendrier renvoie des chemins du type :
        'Sancti/10-24'      -> '10-24'
        'Sancti/10-DU'      -> '10-DU'
        'Tempora/Pent21-6'  -> 'Pent21-6'
        'Tempora/Pasc1-0'   -> 'Pasc1-0'
        'Tempora/Quadp1-0'  -> 'Quadp1-0'
        'Tempora/Adv1-0'    -> 'Adv1-0'

    On garde donc la même logique : basename sans extension, qui
    correspond aux clés `MM-JJ` et leurs variantes déjà présentes
    dans correspondance.json.
    """
    return Path(fichier).name

# ── Recherche d'un audio pour une section ──────────────────────────────────
def chercher_audio(correspondance: dict,
                   cles_jour: list,
                   mapping: tuple) -> str | None:
    """
    Cherche l'audio d'une section parmi les clés du jour, dans l'ordre
    de priorité donné par `cles_jour`. `mapping` liste les champs
    possibles dans la sous-entrée (ex : ('alleluia', 'trait')).

    Renvoie la première valeur `audio` non vide trouvée, sinon None.
    Ne lève jamais d'exception.
    """
    if not correspondance or not cles_jour or not mapping:
        return None
    for cle_j in cles_jour:
        entree = correspondance.get(cle_j)
        if not isinstance(entree, dict):
            continue
        for champ in mapping:
            sous = entree.get(champ)
            if isinstance(sous, dict):
                audio = sous.get("audio")
                if audio:                # non vide et non None
                    return audio
    return None

# ── Fonction principale ─────────────────────────────────────────────────────
def messe(d: date) -> dict:
    """Génère le contenu complet de la messe pour la date `d` (JSON)."""
    fichiers = fichiers_du_jour(d)
    nom, classe, note = celebration(d)

    cles_jour = [cle_jour(f) for f in fichiers]
    correspondance = charger_correspondance(FICHIER_CORRESPONDANCE)

    propres = {
        "Latin":    propre_du_jour(d, "Latin",    fichiers),
        "Francais": propre_du_jour(d, "Francais", fichiers),
    }

    sections = []
    for cle, titre, langues in PLAN:
        textes = {l: propres[l][cle] for l in langues
                  if propres[l].get(cle)}
        if not textes:
            continue

        audios = None
        if cle in MAPPING_AUDIO:
            audios = chercher_audio(correspondance, cles_jour,
                                    MAPPING_AUDIO[cle])

        sections.append({
            "cle":    cle,
            "titre":  titre,
            "textes": textes,
            "audios": audios,
        })

    return {
        "date":        d.isoformat(),
        "celebration": {"nom": nom, "classe": classe, "note": note},
        "fichiers":    fichiers,
        "cles_jour":   cles_jour,
        "sections":    sections,
    }

# ── Écriture des fichiers JSON ─────────────────────────────────────────────
def ecrire_messe(d: date, dossier: Path = DOSSIER_SORTIE) -> Path:
    """Écrit messes/AAAA-MM-JJ.json et renvoie le chemin du fichier."""
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{d.isoformat()}.json"
    chemin.write_text(
        json.dumps(messe(d), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return chemin

def ecrire_annee(annee: int, dossier: Path = DOSSIER_SORTIE) -> int:
    """
    Écrit un JSON par jour de l'année. Une erreur sur un jour est
    signalée sur stderr mais n'interrompt pas le reste.
    Renvoie le nombre de fichiers écrits.
    """
    ecrits, erreurs = 0, 0
    d = date(annee, 1, 1)
    un_jour = timedelta(days=1)
    while d.year == annee:
        try:
            ecrire_messe(d, dossier)
            ecrits += 1
        except Exception as exc:                    # noqa: BLE001
            erreurs += 1
            print(f"  !! {d.isoformat()} : {type(exc).__name__}: {exc}",
                  file=sys.stderr)
        d += un_jour
    print(f"{ecrits} fichiers écrits dans {dossier} ({erreurs} erreur(s))")
    return ecrits

# ── Tests de non-régression ────────────────────────────────────────────────
DATES_TEST = [
    ("2026-10-24", "Date avec entrée 10-24 dans correspondance"),
    ("2026-04-12", "Date sans entrée (Quasimodo, Pasc1-0 présent "
                   "mais on veut aussi un cas où aucune correspondance "
                   "n'est trouvée pour une des sections)"),
]

def lancer_tests() -> int:
    """
    Exécute messe() pour chaque date de DATES_TEST, imprime un résumé.
    Renvoie 0 si aucune exception, 1 sinon.
    """
    echecs = 0
    for iso, descr in DATES_TEST:
        y, m, j = map(int, iso.split("-"))
        d = date(y, m, j)
        print(f"\n=== Test : {iso} — {descr} ===")
        try:
            resultat = messe(d)
        except Exception as exc:                    # noqa: BLE001
            echecs += 1
            print(f"  !! Exception : {type(exc).__name__}: {exc}")
            continue
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
    print(f"\n--- Bilan : {len(DATES_TEST) - echecs}/{len(DATES_TEST)} OK ---")
    return 0 if echecs == 0 else 1

# ── Point d'entrée ──────────────────────────────────────────────────────────
USAGE = """Usage :
  python messe.py AAAA-MM-JJ            affiche le JSON du jour
  python messe.py AAAA-MM-JJ --ecrire   écrit messes/AAAA-MM-JJ.json
  python messe.py annee AAAA            écrit un JSON pour chaque jour de l'année
  python messe.py test                  tests de non-régression"""

if __name__ == "__main__":
    args = sys.argv[1:]

    if args == ["test"]:
        sys.exit(lancer_tests())

    if len(args) == 2 and args[0] == "annee":
        ecrire_annee(int(args[1]))
        sys.exit(0)

    if len(args) in (1, 2) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", args[0]):
        y, m, j = map(int, args[0].split("-"))
        d = date(y, m, j)
        if len(args) == 1:
            print(json.dumps(messe(d), ensure_ascii=False, indent=2))
            sys.exit(0)
        if args[1] == "--ecrire":
            print(ecrire_messe(d))
            sys.exit(0)

    sys.exit(USAGE)
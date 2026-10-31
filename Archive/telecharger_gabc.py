#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telecharger_gabc.py — Télécharge les .gabc depuis Gregobase.

Entrée : incipits latins (Introitus / Graduale / Offertorium / Communio)
         soit depuis un fichier d'incipits (1 par ligne, ou avec préfixe),
         soit depuis les data/Latin/* (sections [Introitus] [Graduale]
         [Offertorium] [Communio]) en explorant l'arborescence.

Sortie : gabc/<cle>.gabc  avec cle = '<section>_<3-premiers-mots-slug>'.

Politesse : User-Agent identifiant le projet, délai entre requêtes,
            reprise sur erreur, journal des manquants.

Filtrage : on essaie de privilégier les sources 'Graduale Romanum 1908'
            et 'Graduale Romanum 1961'. Si aucune correspondance de
            source n'est trouvée, on prend le 1er résultat.

Usage :
   python telecharger_gabc.py --incipits incipits.txt
   python telecharger_gabc.py --data data/Latin
   python telecharger_gabc.py --data data/Latin --dry-run   # n'écrit pas les gabc
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

GREGO_SEARCH = "https://gregobase.selapa.net/search.php"
GREGO_DOWNLOAD = "https://gregobase.selapa.net/download.php"
USER_AGENT = "Missale1962/0.1 (+https://github.com/local/messe1962)"
DELAI = 1.5   # secondes entre 2 requêtes
TIMEOUT = 30
MAX_RETRIES = 3

PREFIXE = {
    "Introitus":   "introitus",
    "Graduale":    "graduel",
    "GradualeP":   "graduel",
    "Alleluia":    "graduel",
    "Tractus":     "graduel",
    "Offertorium": "offertoire",
    "Communio":    "communion",
}


# ---------------- normalisation ----------------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def slug_incipit(texte: str, limite_mots: int = 3) -> str:
    s = strip_accents(texte).lower()
    s = re.sub(r"[^a-z0-9']+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    return "-".join(s.split(" ")[:limite_mots])[:60]


def cle_fichier(prefixe: str, incipit: str) -> str:
    return f"{prefixe}_{slug_incipit(incipit)}"


# ---------------- collecte des incipits ----------------
_RE_SECTION = re.compile(r"^\[(\w+)\]\s*$")


def lire_sections(chemin: Path) -> dict[str, str]:
    if not chemin.exists():
        return {}
    texte = chemin.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}
    courant, tampon = None, []
    for ligne in texte.splitlines():
        m = _RE_SECTION.match(ligne)
        if m:
            if courant is not None:
                out[courant] = "\n".join(tampon).strip()
            courant, tampon = m.group(1), []
        elif courant is not None:
            tampon.append(ligne)
    if courant is not None:
        out[courant] = "\n".join(tampon).strip()
    return out


def premier_incipit(texte: str) -> str:
    out: list[str] = []
    for ligne in texte.splitlines():
        s = ligne.strip()
        if not s or s.startswith(("!", "&", "@", "*", "~", "#")):
            continue
        s = re.sub(r"\s+", " ", s)
        if not s:
            continue
        out.append(s)
        if len(" ".join(out).split()) >= 3:
            break
    return " ".join(" ".join(out).strip().rstrip(".,;:").split()[:3])


def collect_incipits(data_dir: Path | None,
                     incipits_file: Path | None) -> list[tuple[str, str]]:
    """Retourne [(prefixe, incipit), ...]."""
    out: list[tuple[str, str]] = []
    if incipits_file and incipits_file.exists():
        for ligne in incipits_file.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            # format : "Introitus : Accipite..." ou juste "Accipite..."
            if ":" in ligne or "：" in ligne:
                entete, incipit = re.split(r"[:：]", ligne, 1)
                entete = entete.strip()
                for k, v in PREFIXE.items():
                    if entete.lower().startswith(k.lower()):
                        out.append((v, incipit.strip()))
                        break
            else:
                out.append(("graduel", ligne))
    if data_dir and data_dir.exists():
        for f in sorted(data_dir.rglob("*.txt")):
            sections = lire_sections(f)
            for k, v in sections.items():
                if k in PREFIXE:
                    inc = premier_incipit(v)
                    if inc:
                        out.append((PREFIXE[k], inc))
    # déduplication par clé
    vu: set[str] = set()
    res: list[tuple[str, str]] = []
    for pref, inc in out:
        cle = cle_fichier(pref, inc)
        if cle and cle not in vu:
            vu.add(cle)
            res.append((pref, inc))
    return res


# ---------------- réseau ----------------
def http_get(url: str, referer: str | None = None) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        **({"Referer": referer} if referer else {}),
    })
    last = None
    for i in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return data.decode("latin-1", errors="replace")
        except Exception as e:  # URLError, HTTPError, timeout...
            last = e
            time.sleep(DELAI * (i + 1))
    raise RuntimeError(f"GET {url} a échoué : {last}")


def chercher_id(incipit: str) -> list[int]:
    """Cherche un incipit sur Gregobase, retourne la liste d'IDs trouvés."""
    url = f"{GREGO_SEARCH}?query={urllib.parse.quote(incipit)}&type=incipit"
    html = http_get(url)
    ids: list[int] = []
    for m in re.finditer(r"[?&]id=(\d+)", html):
        try:
            ids.append(int(m.group(1)))
        except ValueError:
            pass
    # déduplique en gardant l'ordre
    vu, out = set(), []
    for i in ids:
        if i not in vu:
            vu.add(i)
            out.append(i)
    return out


def telecharger_gabc(gabc_id: int) -> str | None:
    """Télécharge le .gabc. Renvoie le contenu texte ou None."""
    url = f"{GREGO_DOWNLOAD}?id={gabc_id}&format=gabc"
    try:
        txt = http_get(url, referer=GREGO_SEARCH)
    except Exception:
        return None
    # gabc brut commence par des en-têtes %%, commentaire; sinon page HTML
    if txt.lstrip().startswith(("%%", "name:", "%%commentator")) or "gabc" in txt[:200].lower():
        return txt
    # Si c'est une page HTML, on cherche un lien gabc
    m = re.search(r'href="([^"]*download\.php\?[^"]*format=gabc[^"]*)"', txt)
    if m:
        return http_get("https://gregobase.selapa.net/" + m.group(1).lstrip("/"),
                        referer=url)
    return None


def filtrer_source(texte: str, sources: list[str]) -> bool:
    """Vrai si le texte mentionne une des sources préférées (1908 / 1961)."""
    if not sources:
        return True
    t = texte.lower()
    return any(s.lower() in t for s in sources)


# ---------------- pipeline ----------------
def telecharger_pour(incipits: list[tuple[str, str]],
                     gabc_dir: Path,
                     manquants: Path,
                     dry_run: bool,
                     sources_preferees: list[str]) -> tuple[int, int]:
    ok, ko = 0, 0
    for prefixe, incipit in incipits:
        cle = cle_fichier(prefixe, incipit)
        cible = gabc_dir / f"{cle}.gabc"
        if cible.exists():
            continue
        try:
            ids = chercher_id(incipit)
        except Exception as e:
            manquants.write_text(
                manquants.read_text(encoding="utf-8") + f"{cle}\t{incipit}\t{type(e).__name__}\n",
                encoding="utf-8",
            )
            ko += 1
            time.sleep(DELAI)
            continue

        contenu = None
        if sources_preferees and ids:
            # essayer chaque ID, garder celui qui mentionne une source préférée
            for gid in ids:
                txt = telecharger_gabc(gid)
                if txt and filtrer_source(txt, sources_preferees):
                    contenu = txt
                    break
                time.sleep(0.2)
        if contenu is None and ids:
            contenu = telecharger_gabc(ids[0])
        if contenu:
            if not dry_run:
                gabc_dir.mkdir(parents=True, exist_ok=True)
                cible.write_text(contenu, encoding="utf-8")
            ok += 1
        else:
            manquants.write_text(
                manquants.read_text(encoding="utf-8") + f"{cle}\t{incipit}\tnon trouvé\n",
                encoding="utf-8",
            )
            ko += 1
        time.sleep(DELAI)
    return ok, ko


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Télécharge les gabc depuis Gregobase.")
    ap.add_argument("--data", type=Path, help="Dossier data/Latin (ou arborescence).")
    ap.add_argument("--incipits", type=Path, help="Fichier d'incipits (1 par ligne).")
    ap.add_argument("--gabc", type=Path, default=Path("gabc"),
                    help="Dossier de sortie (défaut : gabc).")
    ap.add_argument("--manquants", type=Path, default=Path("gabc_manquants.txt"),
                    help="Journal des incipits non trouvés.")
    ap.add_argument("--dry-run", action="store_true",
                    help="N'écrit pas les fichiers .gabc.")
    ap.add_argument("--sources", nargs="+",
                    default=["Graduale Romanum 1908", "Graduale Romanum 1961"],
                    help="Sources préférées (filtrage).")
    args = ap.parse_args(argv[1:])

    incipits = collect_incipits(args.data, args.incipits)
    if not incipits:
        print("Aucun incipit trouvé. Donnez --data ou --incipits.", file=sys.stderr)
        return 2
    print(f"{len(incipits)} incipit(s) à traiter.")

    args.manquants.write_text(
        f"# gabc_manquants — généré {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        encoding="utf-8",
    )
    try:
        ok, ko = telecharger_pour(
            incipits, args.gabc, args.manquants,
            dry_run=args.dry_run, sources_preferees=args.sources,
        )
    except Exception as e:
        print(f"ERREUR réseau : {type(e).__name__}: {e}", file=sys.stderr)
        print("(le sandbox n'a probablement pas accès à gregobase.selapa.net)",
              file=sys.stderr)
        return 3
    print(f"OK={ok}  KO={ko}  dry-run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""
gabc_engine.py
Transforme une chaîne GABC (telle que stockée dans gregobase_chants.gabc)
en partition PDF/PNG via Gregorio.

Prérequis (macOS) :
    brew install gregorio          # fournit la commande `gregorio`
    brew install --cask mactex     # ou basictex, pour lualatex
    brew install poppler           # pour pdftoppm (PNG)

Usage en module :
    from gabc_engine import rendre_gabc
    pdf = rendre_gabc(gabc_brut, nom="Tu es Petrus", dossier="partitions")

Usage en ligne de commande :
    python3 gabc_engine.py fichier.gabc
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Décodage du champ gabc de la base
# ---------------------------------------------------------------------------

def decode_gabc(valeur: Optional[str]) -> Optional[str]:
    """Extrait la partie GABC d'un champ `gabc` de gregobase_chants.

    Le champ est une liste JSON de paires [nom, contenu], par exemple
    [["tex", "..."], ["gabc", "(c4) AL(...)..."]].
    Retourne le contenu de la paire "gabc", ou None.
    """
    if not valeur:
        return None
    try:
        paires = json.loads(valeur)
    except (ValueError, TypeError):
        # Déjà du GABC brut
        return valeur
    if isinstance(paires, list):
        for paire in paires:
            if isinstance(paire, list) and len(paire) >= 2 and paire[0] == "gabc":
                return paire[1]
    return None

# ---------------------------------------------------------------------------
# En-tête GABC
# ---------------------------------------------------------------------------

EN_TETE_DEFAUT = {
    "name": "Chant",
    "mode": "1",
    "transcriber": "Généré",
    "gabc-copyright": "Domaine public",
    "book": "Graduale",
}

def separer_entete(gabc: str) -> tuple[dict, str]:
    """Sépare l'en-tête (clé: valeur;) du corps GABC, séparés par %%."""
    if "%%" in gabc:
        entete_brut, corps = gabc.split("%%", 1)
    else:
        entete_brut, corps = "", gabc
    entete = {}
    for ligne in entete_brut.splitlines():
        m = re.match(r"\s*([\w\-]+)\s*:\s*(.*?);?\s*$", ligne)
        if m:
            entete[m.group(1)] = m.group(2)
    return entete, corps.strip()

def construire_gabc(gabc_corps: str, nom: str, mode: Optional[str] = None,
                    entete_extra: Optional[dict] = None) -> str:
    """Assemble un fichier .gabc complet : en-tête puis %% puis corps."""
    entete_src, corps = separer_entete(gabc_corps)
    entete = {**EN_TETE_DEFAUT, **entete_src, **(entete_extra or {})}
    entete["name"] = nom
    if mode:
        entete["mode"] = str(mode)
    lignes = [f"{cle}: {valeur};" for cle, valeur in entete.items()]
    return "\n".join(lignes) + "\n%%\n" + corps + "\n"

# ---------------------------------------------------------------------------
# Validation légère
# ---------------------------------------------------------------------------

@dataclass
class Diagnostic:
    niveau: str   # "erreur" ou "avertissement"
    message: str

@dataclass
class RapportGabc:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    nb_syllabes: int = 0
    nb_neumes: int = 0

    @property
    def valide(self) -> bool:
        return not any(d.niveau == "erreur" for d in self.diagnostics)

def valider_gabc(gabc_corps: str) -> RapportGabc:
    """Contrôles simples avant de lancer Gregorio."""
    rapport = RapportGabc()
    corps = separer_entete(gabc_corps)[1]

    if not corps:
        rapport.diagnostics.append(Diagnostic("erreur", "corps GABC vide"))
        return rapport

    if corps.count("(") != corps.count(")"):
        rapport.diagnostics.append(Diagnostic(
            "erreur", f"parenthèses déséquilibrées : {corps.count('(')} ouvrantes, "
                      f"{corps.count(')')} fermantes"))

    notations = re.findall(r"\(([^()]*)\)", corps)
    rapport.nb_neumes = len(notations)
    if not notations:
        rapport.diagnostics.append(Diagnostic("erreur", "aucun bloc de notation (...)"))

    rapport.nb_syllabes = len(re.findall(r"[^\s()]+\(", corps))

    balises = set(re.findall(r"<(/?)(\w+)[^>]*>", corps))
    connues = {"i", "b", "c", "sp", "eu", "clear", "ul", "v", "tt"}
    for _, nom in balises:
        if nom not in connues:
            rapport.diagnostics.append(Diagnostic(
                "avertissement", f"balise inconnue <{nom}>"))

    return rapport

# ---------------------------------------------------------------------------
# Rendu via Gregorio
# ---------------------------------------------------------------------------

class GregorioIntrouvable(RuntimeError):
    pass

def _verifier_outils() -> None:
    manquants = [o for o in ("gregorio", "lualatex") if shutil.which(o) is None]
    if manquants:
        raise GregorioIntrouvable(
            "Outil(s) manquant(s) : " + ", ".join(manquants) +
            ". Installer gregorio et MacTeX (voir l'en-tête du module).")

def _lancer(commande: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(commande, cwd=cwd, capture_output=True, text=True)

def rendre_gabc(gabc_brut: str, nom: str, dossier: str | Path = "partitions",
                mode: Optional[str] = None, png: bool = True,
                garder_source: bool = True) -> Path:
    """Transforme une chaîne GABC en PDF (et PNG optionnel).

    Retourne le chemin du PDF. Lève ValueError si la validation échoue,
    GregorioIntrouvable si les outils ne sont pas installés, RuntimeError
    si Gregorio ou LaTeX échouent.
    """
    gabc_corps = decode_gabc(gabc_brut) or gabc_brut
    rapport = valider_gabc(gabc_corps)
    if not rapport.valide:
        msgs = "; ".join(d.message for d in rapport.diagnostics if d.niveau == "erreur")
        raise ValueError(f"GABC invalide ({nom}) : {msgs}")
    for d in rapport.diagnostics:
        print(f"[{d.niveau}] {nom} : {d.message}", file=sys.stderr)

    _verifier_outils()

    sortie = Path(dossier).resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", nom).strip("_") or "chant"
    gabc_final = construire_gabc(gabc_corps, nom=nom, mode=mode)

    # Tout se fait dans le dossier de sortie : Gregorio et LaTeX
    # trouvent alors leurs fichiers (\input, .aux, .gaux) au même endroit.
    # Le dossier _debug garde une copie du .tex pour inspection.
    travail = sortie / "_debug"
    travail.mkdir(parents=True, exist_ok=True)

    src = travail / f"{slug}.gabc"
    src.write_text(gabc_final, encoding="utf-8")

    # 1) GABC -> LaTeX
    r = _lancer(["gregorio", "-o", f"{slug}.tex", src.name], cwd=travail)
    tex = travail / f"{slug}.tex"
    if r.returncode != 0 or not tex.exists():
        raise RuntimeError(
            f"gregorio a échoué (code {r.returncode}).\n"
            f"stdout : {r.stdout}\nstderr : {r.stderr}\n"
            f"GABC envoyé :\n{gabc_final}"
        )
    # 1bis) Enveloppe le fragment dans un document complet
    enveloppe = (
        "\\documentclass[a4paper,12pt]{article}\n"
        "\\usepackage{gregoriotex}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n"
        f"\\input{{{slug}.tex}}\n"
        "\\end{document}\n"
    )
    doc = travail / f"{slug}_doc.tex"
    doc.write_text(enveloppe, encoding="utf-8")
    # 2) LaTeX -> PDF, deux passes (Gregorio demande une relance)
    for _ in range(2):
        r = _lancer(["lualatex", "-interaction=nonstopmode", doc.name], cwd=travail)
        if r.returncode != 0:
            raise RuntimeError(
                f"lualatex a échoué (code {r.returncode}).\n"
                f"{r.stdout[-3000:]}"
            )

    pdf_travail = travail / f"{slug}_doc.pdf"
    if not pdf_travail.exists():
        raise RuntimeError(f"lualatex n'a pas produit {pdf_travail.name}")

    pdf_final = sortie / f"{slug}.pdf"
    shutil.copy(pdf_travail, pdf_final)
    if garder_source:
        shutil.copy(src, sortie / f"{slug}.gabc")

    # 3) PDF -> PNG (première page)
    if png and shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-r", "150",
                        str(pdf_final), str(sortie / slug)],
                       check=True, capture_output=True)

    return pdf_final

# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage : gabc_engine.py fichier.gabc [dossier_sortie]", file=sys.stderr)
        return 2
    chemin = Path(argv[1])
    dossier = argv[2] if len(argv) > 2 else "partitions"
    brut = chemin.read_text(encoding="utf-8")
    try:
        pdf = rendre_gabc(brut, nom=chemin.stem, dossier=dossier)
    except (ValueError, GregorioIntrouvable, RuntimeError,
            subprocess.CalledProcessError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    print(f"Partition écrite : {pdf}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
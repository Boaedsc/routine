#!/usr/bin/env python3
"""Rend chaque .gabc en plusieurs SVG (une variante par largeur de référence)."""
import re
import subprocess
from pathlib import Path

GABC = Path("gabc")
SORTIE = Path("partitions")
LARGEURS = [480, 768, 1024]   # px : seuils où la mise en page change
SORTIE.mkdir(exist_ok=True)


def rendre_fluide(svg_path: Path, largeur: int) -> None:
    """Fixe la largeur de référence pour la mise en page, puis retire les dimensions absolues."""
    txt = svg_path.read_text(encoding="utf-8")
    txt = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', rf'\1 data-largeur="{largeur}"', txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r'\1', txt, count=1)
    svg_path.write_text(txt, encoding="utf-8")


def generer(src: Path, largeur: int) -> Path:
    cible = SORTIE / f"{src.stem}-{largeur}.svg"
    if cible.exists() and cible.stat().st_mtime >= src.stat().st_mtime:
        return cible
    # gabc2svg : option de largeur de page à adapter à ta version de gregorio
    subprocess.run(
        ["gabc2svg", "--width", str(largeur), str(src), str(cible)],
        check=True,
    )
    rendre_fluide(cible, largeur)
    print("rendu :", cible)
    return cible


for src in sorted(GABC.glob("*.gabc")):
    for l in LARGEURS:
        generer(src, l)
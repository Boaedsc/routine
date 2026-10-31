import json
import re
import sys
import unicodedata
from datetime import date, timedelta

import calendrier  # ton fichier calendrier.py

fichier = sys.argv[1] if len(sys.argv) > 1 else "reference-2026.json"

with open(fichier, encoding="utf-8") as f:
    donnees = json.load(f)


def extraire_jours(obj):
    """Récupère les objets de jour, que le JSON soit une liste ou un objet."""
    if isinstance(obj, dict):
        if isinstance(obj.get("day"), dict) and "date" in obj["day"]:
            yield obj["day"]
        else:
            for valeur in obj.values():
                yield from extraire_jours(valeur)
    elif isinstance(obj, list):
        for valeur in obj:
            yield from extraire_jours(valeur)


def normaliser(texte):
    texte = re.sub(r"<[^>]+>", "", str(texte))  # retire le HTML
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return " ".join(texte.casefold().split())


reference = {}

for jour in donnees.get("days", []):
    celebration = jour.get("celebration") or {}
    reference[jour["date"]] = celebration

if not reference:
    raise SystemExit("Aucun jour trouvé dans la clé 'days' du JSON.")
annee = int(next(iter(reference))[:4])
d = date(annee, 1, 1)
nb_erreurs = 0

while d.year == annee:
    iso = d.isoformat()
    api = reference.get(iso)

    if api is None:
        print(f"{iso} | ABSENT de la réponse API")
        nb_erreurs += 1
    else:
        nom_code, classe_code, note = calendrier.celebration(d)
        nom_api = api.get("name", "")
        rang_api = api.get("rank", "")

        # L’API peut représenter certains rangs comme du texte.
        classe_api = int(rang_api) if str(rang_api).isdigit() else None

        nom_ok = normaliser(nom_code) == normaliser(nom_api)
        classe_ok = classe_code == classe_api

        if not nom_ok or not classe_ok:
            print(
                f"{iso} | DIFFÉRENCE\n"
                f"  ton code : classe {classe_code}, {nom_code} {note}\n"
                f"  API      : classe {rang_api}, {nom_api}"
            )
            nb_erreurs += 1

    d += timedelta(days=1)

print(f"\nComparaison terminée : {nb_erreurs} différence(s).")
#!/usr/bin/env python3
"""
Calendrier liturgique perpétuel, rubriques de 1960 (missel de 1962).
Tout ce qui est "donnée" est dans des tables en haut : corrigez-les à la main.
Usage : python calendrier.py 2026-10-24     |     python calendrier.py 2026   (année entière)
"""
from datetime import date, timedelta
import sys
from pathlib import Path


JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
ROMAIN = {1: "I", 2: "II", 3: "III", 4: "IV"}

# ======================================================================
# TABLES DE DONNÉES  (à corriger à la main)
# ======================================================================

# Sanctoral : (mois, jour) -> (nom, classe, [drapeaux])
# drapeaux : "seigneur" = fête du Seigneur (bat un dimanche de cl. II)
#            "dim_I"    = ne peut pas être transférée (omise si empêchée)
SANCTORAL = {
    # JANVIER
    (1, 1): ("Circoncision du Seigneur", 2, ["seigneur"]),
    (1, 6): ("Épiphanie du Seigneur", 1, ["seigneur"]),
    (1, 13): ("Commémoration du Baptême du Seigneur", 2, ["seigneur"]),
    (1, 14): ("Saint Hilaire", 3, []),
    (1, 15): ("Saint Paul, premier ermite", 3, []),
    (1, 16): ("Saint Marcel Ier", 3, []),
    (1, 17): ("Saint Antoine, abbé", 3, []),
    (1, 18): ("Chaire de saint Pierre à Rome", 2, []),
    (1, 19): ("Saints Marius, Marthe, Audifax et Abachum", 4, []),
    (1, 20): ("Saints Fabien et Sébastien", 3, []),
    (1, 21): ("Sainte Agnès", 3, []),
    (1, 22): ("Saints Vincent et Anastase", 3, []),
    (1, 23): ("Saint Raymond de Peñafort", 4, []),
    (1, 24): ("Saint Timothée", 3, []),
    (1, 25): ("Conversion de saint Paul", 3, []),
    (1, 26): ("Saint Polycarpe", 3, []),
    (1, 27): ("Saint Jean Chrysostome", 3, []),
    (1, 28): ("Saint Pierre Nolasque", 3, []),
    (1, 29): ("Saint François de Sales", 3, []),
    (1, 30): ("Sainte Martine", 3, []),
    (1, 31): ("Saint Jean Bosco", 3, []),
    # FÉVRIER
    (2, 1): ("Saint Ignace d'Antioche", 3, []),
    (2, 2): ("Purification de la B.V.M.", 2, ["seigneur"]),
    (2, 3): ("Saint Blaise", 4, []),
    (2, 4): ("Saint André Corsini", 3, []),
    (2, 5): ("Sainte Agathe", 3, []),
    (2, 6): ("Sainte Dorothée", 3, []),
    (2, 7): ("Saint Romuald", 3, []),
    (2, 8): ("Saint Jean de Matha", 3, []),
    (2, 9): ("Saint Cyrille d'Alexandrie", 3, []),
    (2, 10): ("Sainte Scholastique", 3, []),
    (2, 11): ("Apparition de la B.V.M. Immaculée (Lourdes)", 3, []),
    (2, 14): ("Saint Valentin", 4, []),
    (2, 15): ("Saints Faustin et Jovite", 4, []),
    (2, 18): ("Saint Siméon", 4, []),
    (2, 22): ("Chaire de saint Pierre à Antioche", 2, []),

    (2, 24): ("Saint Matthias, apôtre", 2, []),
    (2, 27): ("Saint Gabriel de l'Addolorata", 3, []),
    # MARS
    (3, 4): ("Saint Casimir", 3, []),
    (3, 6): ("Saintes Perpétue et Félicité", 3, []),
    (3, 7): ("Saint Thomas d'Aquin", 3, []),
    (3, 8): ("Saint Jean de Dieu", 3, []),
    (3, 9): ("Sainte Françoise Romaine", 3, []),
    (3, 10): ("Les quarante martyrs de Sébaste", 3, []),
    (3, 12): ("Saint Grégoire le Grand", 3, []),
    (3, 17): ("Saint Patrice", 4, []),
    (3, 18): ("Saint Cyrille de Jérusalem", 4, []),
    (3, 19): ("Saint Joseph, Époux de la B.V.M.", 1, ["dim_I"]),
    (3, 21): ("Saint Benoît", 3, []),
    (3, 24): ("Saint Gabriel Archange", 4, []),
    (3, 25): ("Annonciation de la B.V.M.", 1, ["seigneur"]),
    (3, 27): ("Saint Jean Damascène", 3, []),
    # AVRIL
    (4, 2): ("Saint François de Paule", 3, []),
    (4, 4): ("Saint Isidore", 3, []),
    (4, 5): ("Saint Vincent Ferrier", 3, []),
    (4, 11): ("Saint Léon le Grand", 3, []),
    (4, 13): ("Saint Hermenegilde", 4, []),
    (4, 14): ("Saints Tiburce, Valérien et Maxime", 4, []),
    (4, 17): ("Saint Anicet", 4, []),
    (4, 21): ("Saint Anselme", 3, []),
    (4, 22): ("Saints Soter et Caius", 4, []),
    (4, 23): ("Saint Georges", 4, []),
    (4, 24): ("Saint Fidèle de Sigmaringen", 3, []),
    (4, 25): ("Saint Marc, évangéliste", 2, []),
    (4, 26): ("Saints Clet et Marcellin", 4, []),
    (4, 27): ("Saint Pierre Canisius", 3, []),
    (4, 28): ("Saint Paul de la Croix", 3, []),
    (4, 29): ("Saint Pierre de Vérone", 3, []),
    (4, 30): ("Sainte Catherine de Sienne", 3, []),
    # MAI
    (5, 1): ("Saints Philippe et Jacques, apôtres", 2, []),
    (5, 2): ("Saint Athanase", 3, []),
    (5, 3): ("Invention de la Sainte Croix", 3, []),
    (5, 4): ("Sainte Monique", 3, []),
    (5, 5): ("Saint Pie V", 3, []),
    (5, 6): ("Saint Jean devant la Porte Latine", 3, []),
    (5, 7): ("Saint Stanislas", 3, []),
    (5, 8): ("Apparition de saint Michel", 3, []),
    (5, 9): ("Saint Grégoire de Nazianze", 3, []),
    (5, 10): ("Saint Antonin", 3, []),
    (5, 12): ("Saints Nérée, Achillée et Pancrace", 4, []),
    (5, 13): ("Saint Robert Bellarmin", 3, []),
    (5, 14): ("Saint Boniface", 4, []),
    (5, 15): ("Saint Jean-Baptiste de La Salle", 3, []),
    (5, 18): ("Saint Venance", 4, []),
    (5, 19): ("Saint Pierre Célestin", 3, []),
    (5, 20): ("Saint Bernardin de Sienne", 3, []),
    (5, 25): ("Saint Grégoire VII", 3, []),
    (5, 26): ("Saint Philippe Néri", 3, []),
    (5, 27): ("Saint Bède le Vénérable", 3, []),
    (5, 30): ("Saint Félix Ier", 4, []),
    # JUIN
    (6, 1): ("Saint Ange Custode", 4, []),
    (6, 2): ("Saints Marcellin et Pierre", 4, []),
    (6, 4): ("Saint François Caracciolo", 3, []),
    (6, 5): ("Saint Boniface", 3, []),
    (6, 6): ("Saint Norbert", 3, []),
    (6, 9): ("Saints Primus et Félicien", 4, []),
    (6, 10): ("Sainte Marguerite de Hongrie", 4, []),
    (6, 11): ("Saint Barnabé, apôtre", 2, []),
    (6, 12): ("Saint Jean de Sahagún", 3, []),
    (6, 13): ("Saint Antoine de Padoue", 3, []),
    (6, 14): ("Saint Basile le Grand", 3, []),
    (6, 15): ("Saints Vit, Modeste et Crescence", 4, []),

    (6, 18): ("Saint Éphrem", 4, []),
    (6, 19): ("Saint Jean-Marie Vianney", 3, []),
    (6, 21): ("Saint Louis de Gonzague", 3, []),
    (6, 22): ("Saint Paulin de Nole", 3, []),
    (6, 24): ("Nativité de saint Jean-Baptiste", 1, ["dim_I"]),
    (6, 26): ("Saints Jean et Paul", 4, []),
    (6, 28): ("Saint Irénée", 3, []),
    (6, 29): ("Saints Pierre et Paul", 1, ["dim_I"]),
    (6, 30): ("Commémoration de saint Paul", 3, []),
    # JUILLET
    (7, 1): ("Précieux Sang de N.S.", 1, ["seigneur"]),
    (7, 2): ("Visitation de la B.V.M.", 2, []),
    (7, 3): ("Saint Léon II", 4, []),
    (7, 5): ("Saint Antoine-Marie Zaccaria", 3, []),
    (7, 8): ("Sainte Élisabeth de Portugal", 4, []),
    (7, 10): ("Les sept frères martyrs", 4, []),
    (7, 11): ("Saint Pie Ier", 4, []),
    (7, 12): ("Saint Jean Gualbert", 4, []),
    (7, 14): ("Saint Bonaventure", 3, []),
    (7, 15): ("Saint Henri", 4, []),
    (7, 16): ("Notre-Dame du Mont-Carmel", 3, []),
    (7, 17): ("Saint Alexis", 4, []),
    (7, 18): ("Saint Camille de Lellis", 3, []),
    (7, 19): ("Saint Vincent de Paul", 3, []),
    (7, 20): ("Saint Jérôme Émilien", 3, []),
    (7, 21): ("Saint Laurent de Brindisi", 3, []),
    (7, 22): ("Sainte Marie-Madeleine", 3, []),
    (7, 23): ("Saint Apollinaire", 3, []),
    (7, 24): ("Sainte Christine", 3, []),
    (7, 25): ("Saint Jacques le Majeur, apôtre", 2, []),
    (7, 26): ("Sainte Anne, mère de la B.V.M.", 2, []),
    (7, 27): ("Saint Pantaléon", 4, []),
    (7, 28): ("Saints Nazaire, Celse, Victor et Innocent", 4, []),
    (7, 29): ("Sainte Marthe", 3, []),
    (7, 30): ("Saints Abdon et Sennen", 4, []),
    (7, 31): ("Saint Ignace de Loyola", 3, []),
    # AOÛT
    (8, 1): ("Saint Pierre-ès-Liens", 3, []),
    (8, 2): ("Saint Alphonse-Marie de Liguori", 3, []),
    (8, 3): ("Invention de saint Étienne", 4, []),
    (8, 4): ("Saint Dominique", 3, []),
    (8, 5): ("Dédicace de Sainte-Marie des Neiges", 3, []),
    (8, 6): ("Transfiguration de N.S.J.C.", 2, ["seigneur"]),
    (8, 7): ("Saint Gaétan", 3, []),
    (8, 8): ("Saints Cyriaque, Large et Smaragde", 4, []),
    (8, 10): ("Saint Laurent", 2, []),
    (8, 11): ("Saints Tiburce et Suzanne", 4, []),
    (8, 12): ("Sainte Claire", 3, []),
    (8, 13): ("Saints Hippolyte et Cassien", 4, []),
    (8, 14): ("Vigile de l'Assomption", 2, []),
    (8, 15): ("Assomption de la B.V.M.", 1, ["dim_I"]),
    (8, 16): ("Saint Joachim", 3, []),
    (8, 17): ("Saint Hyacinthe", 3, []),
    (8, 19): ("Saint Jean Eudes", 3, []),
    (8, 20): ("Saint Bernard", 3, []),
    (8, 21): ("Sainte Jeanne de Chantal", 3, []),
    (8, 22): ("Cœur Immaculé de Marie", 3, []),
    (8, 23): ("Saint Philippe Béniti", 3, []),
    (8, 24): ("Saint Barthélemy, apôtre", 2, []),
    (8, 25): ("Saint Louis, roi de France", 3, []),
    (8, 26): ("Saint Zéphyrin", 4, []),
    (8, 27): ("Saint Joseph Calasanz", 3, []),
    (8, 28): ("Saint Augustin", 3, []),
    (8, 29): ("Décollation de saint Jean-Baptiste", 3, []),
    (8, 30): ("Sainte Rose de Lima", 3, []),
    (8, 31): ("Saint Raymond Nonnat", 3, []),
    # SEPTEMBRE
    (9, 1): ("Saint Gilles", 4, []),
    (9, 2): ("Saint Étienne de Hongrie", 4, []),
    (9, 5): ("Saint Laurent Justinien", 3, []),
    (9, 8): ("Nativité de la B.V.M.", 2, []),
    (9, 9): ("Saint Gorgonius", 4, []),
    (9, 10): ("Saint Nicolas de Tolentino", 3, []),
    (9, 12): ("Saint Nom de Marie", 3, []),
    (9, 14): ("Exaltation de la Sainte Croix", 2, ["seigneur"]),
    (9, 15): ("Notre-Dame des Sept Douleurs", 3, []),
    (9, 16): ("Saints Corneille et Cyprien", 3, []),
    (9, 17): ("Stigmates de saint François", 3, []),
    (9, 18): ("Saint Joseph de Cupertino", 3, []),
    (9, 19): ("Saint Janvier", 3, []),
    (9, 20): ("Saint Eustache et ses compagnons", 3, []),
    (9, 21): ("Saint Matthieu, apôtre", 2, []),
    (9, 22): ("Saint Thomas de Villeneuve", 3, []),
    (9, 23): ("Saint Lin", 3, []),
    (9, 24): ("Notre-Dame de la Merci", 3, []),
    (9, 26): ("Saints Cyprien et Justine", 4, []),
    (9, 27): ("Saints Côme et Damien", 3, []),
    (9, 28): ("Saint Venceslas", 3, []),
    (9, 29): ("Dédicace de saint Michel Archange", 1, ["dim_I"]),
    (9, 30): ("Saint Jérôme", 3, []),
    # OCTOBRE
    (10, 1): ("Saint Remi", 3, []),
    (10, 2): ("Saints Anges Gardiens", 3, []),
    (10, 3): ("Sainte Thérèse de l'Enfant-Jésus", 3, []),
    (10, 4): ("Saint François d'Assise", 3, []),
    (10, 5): ("Saint Placide", 4, []),
    (10, 6): ("Saint Bruno", 3, []),
    (10, 7): ("Notre-Dame du Rosaire", 2, []),
    (10, 8): ("Sainte Brigitte", 4, []),
    (10, 9): ("Saint Jean Léonardi", 4, []),
    (10, 10): ("Saint François de Borgia", 3, []),
    (10, 11): ("Maternité de la B.V.M.", 2, []),
    (10, 13): ("Saint Édouard", 4, []),
    (10, 14): ("Saint Callixte", 3, []),
    (10, 15): ("Sainte Thérèse d'Avila", 3, []),
    (10, 16): ("Sainte Edwige", 4, []),
    (10, 17): ("Sainte Marguerite-Marie Alacoque", 3, []),
    (10, 18): ("Saint Luc, évangéliste", 2, []),
    (10, 19): ("Saint Pierre d'Alcantara", 3, []),
    (10, 20): ("Saint Jean de Kenty", 3, []),
    (10, 21): ("Saint Hilarion", 4, []),
    (10, 24): ("Saint Raphaël Archange", 3, []),
    (10, 25): ("Saints Chrysanthe et Darie", 4, []),
    (10, 26): ("Saint Évariste", 4, []),
    (10, 28): ("Saints Simon et Jude, apôtres", 2, []),
    (10, 31): ("Vigile de la Toussaint", 3, []),
    # NOVEMBRE
    (11, 1): ("Toussaint", 1, ["dim_I"]),
    (11, 2): ("Commémoration de tous les fidèles défunts", 1, []),
    (11, 4): ("Saint Charles Borromée", 3, []),
    (11, 9): ("Dédicace de la basilique du Latran", 2, ["seigneur"]),
    (11, 10): ("Saint André Avellin", 3, []),
    (11, 11): ("Saint Martin", 3, []),
    (11, 12): ("Saint Martin Ier", 4, []),
    (11, 13): ("Saint Didace", 3, []),
    (11, 14): ("Saint Josaphat", 3, []),
    (11, 15): ("Saint Albert le Grand", 3, []),
    (11, 16): ("Sainte Gertrude", 3, []),
    (11, 17): ("Saint Grégoire Thaumaturge", 3, []),
    (11, 18): ("Dédicace des basiliques de Saint-Pierre et Saint-Paul", 3, []),
    (11, 19): ("Sainte Élisabeth de Hongrie", 3, []),
    (11, 20): ("Saint Félix de Valois", 3, []),
    (11, 21): ("Présentation de la B.V.M.", 3, []),
    (11, 22): ("Sainte Cécile", 3, []),
    (11, 23): ("Saint Clément Ier", 3, []),
    (11, 24): ("Saint Jean de la Croix", 3, []),
    (11, 25): ("Sainte Catherine d'Alexandrie", 3, []),
    (11, 26): ("Saint Silvestre", 3, []),
    (11, 29): ("Saint Saturnin", 4, []),
    (11, 30): ("Saint André, apôtre", 2, []),
    # DÉCEMBRE
    (12, 2): ("Sainte Bibiane", 4, []),
    (12, 3): ("Saint François-Xavier", 3, []),
    (12, 4): ("Saint Pierre Chrysologue", 3, []),
    (12, 5): ("Saint Sabbas", 4, []),
    (12, 6): ("Saint Nicolas", 3, []),
    (12, 7): ("Saint Ambroise", 3, []),
    (12, 8): ("Immaculée Conception de la B.V.M.", 1, []),
    (12, 10): ("Notre-Dame de Lorette", 4, []),
    (12, 11): ("Saint Damase Ier", 3, []),
    (12, 13): ("Sainte Lucie", 3, []),
    (12, 21): ("Saint Thomas, apôtre", 2, []),
    (12, 24): ("Vigile de Noël", 1, []),
    (12, 25): ("Nativité de N.S.J.C.", 1, ["seigneur", "dim_I"]),
    (12, 26): ("Saint Étienne, premier martyr", 2, []),
    (12, 27): ("Saint Jean, apôtre et évangéliste", 2, []),
    (12, 28): ("Saints Innocents", 2, []),
    (12, 29): ("Saint Thomas de Cantorbéry", 3, []),
    (12, 31): ("Saint Silvestre Ier", 3, []),
}
# ======================================================================
# CALCULS DE BASE
# ======================================================================

def paques(annee):
    """Pâques grégorien (Meeus/Jones/Butcher)."""
    a = annee % 19
    b, c = divmod(annee, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois = (h + l - 7 * m + 114) // 31
    jour = ((h + l - 7 * m + 114) % 31) + 1
    return date(annee, mois, jour)

def dim_sur_ou_avant(d):
    return d - timedelta(days=d.isoweekday() % 7)

def dim_apres(d):
    return d + timedelta(days=7 - d.isoweekday() % 7)

def avent1(annee):
    """1er dimanche de l'Avent : dimanche le plus proche du 30 novembre."""
    s = date(annee, 11, 30)
    wd = s.isoweekday() % 7           # 0 = dimanche
    return s - timedelta(days=wd) if wd <= 3 else s + timedelta(days=7 - wd)

def dates_cles(a):
    p = paques(a)
    return {
        "paques": p,
        "septuagesime": p - timedelta(days=63),
        "cendres": p - timedelta(days=46),
        "rameaux": p - timedelta(days=7),
        "ascension": p + timedelta(days=39),
        "pentecote": p + timedelta(days=49),
        "trinite": p + timedelta(days=56),
        "corpus": p + timedelta(days=60),
        "sacre_coeur": p + timedelta(days=68),
        "avent1": avent1(a),
        "christ_roi": date(a, 10, 31) - timedelta(days=date(a, 10, 31).isoweekday() % 7),
    }

# ======================================================================
# TEMPOREL : (nom, classe, categorie)
# ======================================================================

def temporal(d):
    a = d.year
    k = dates_cles(a)
    p = k["paques"]
    wd = d.isoweekday()
    nj = JOURS[wd - 1]
    dim = (wd == 7)

    # --- Avent (jusqu'au 24 déc.) ---
    if k["avent1"] <= d <= date(a, 12, 24):
        n = (d - k["avent1"]).days // 7 + 1
        if dim:
            return (f"{n}e dimanche de l'Avent", 1, "avent")
        if d.day >= 17:
            return (f"{nj} avant Noël ({d.day} déc.)", 2, "avent")
        return (f"{nj} de la {n}e semaine de l'Avent", 3, "avent")

    # --- Octave de Noël et jours suivants ---
    if d == date(a, 12, 25):
        return ("Nativité de N.S.J.C.", 1, "noel")
    if date(a, 12, 26) <= d <= date(a, 12, 31):
        if dim:
            return ("Dimanche dans l'octave de Noël", 2, "noel")
        return (f"{nj} dans l'octave de Noël", 3, "noel")
    if d == date(a, 1, 1):
        return ("Octave de Noël / Circoncision", 2, "noel")
    if date(a, 1, 2) <= d < date(a, 1, 6):
        if dim:
            return ("Très Saint Nom de Jésus", 2, "noel")
        return (f"{nj} avant l'Épiphanie", 4, "noel")
    if d == date(a, 1, 6):
        return ("Épiphanie du Seigneur", 1, "epiphanie")

    # --- Épiphanie -> Septuagésime ---
    if date(a, 1, 6) < d < k["septuagesime"]:
        if dim:
            n = (d - date(a, 1, 6)).days // 7 + 1
            if d == dim_apres(date(a, 1, 6)):
                return ("Sainte Famille", 2, "epiphanie")
            return (f"{n}e dimanche après l'Épiphanie", 2, "epiphanie")
        return (f"{nj} après l'Épiphanie", 4, "epiphanie")

    # --- Septuagésime ---
    if k["septuagesime"] <= d < k["cendres"]:
        if dim:
            noms = ["Septuagésime", "Sexagésime", "Quinquagésime"]
            return (noms[(d - k["septuagesime"]).days // 7], 2, "septuagesime")
        return (f"{nj} après la Septuagésime", 4, "septuagesime")

    # --- Carême ---
    if k["cendres"] <= d < k["rameaux"]:
        if d == k["cendres"]:
            return ("Mercredi des Cendres", 1, "careme")
        if d < k["cendres"] + timedelta(days=4):
            return (f"{nj} après les Cendres", 3, "careme")
        n = (d - (k["cendres"] + timedelta(days=4))).days // 7 + 1
        if dim:
            return (("Dimanche de la Passion" if n == 5 else f"{n}e dimanche de Carême"), 1, "careme")
        if n == 5:
            return (f"{nj} de la semaine de la Passion", 3, "careme")
        return (f"{nj} de la {n}e semaine de Carême", 3, "careme")

    # --- Semaine Sainte ---
    if k["rameaux"] <= d < p:
        noms = ["Dimanche des Rameaux", "Lundi saint", "Mardi saint", "Mercredi saint",
                "Jeudi saint", "Vendredi saint", "Samedi saint"]
        return (noms[(d - k["rameaux"]).days], 1, "semaine_sainte")

    # --- Temps pascal ---
    if p <= d <= k["pentecote"]:
        i = (d - p).days
        if i == 0: return ("Dimanche de Pâques", 1, "pascal")
        if i < 7:  return (f"{nj} dans l'octave de Pâques", 1, "pascal")
        if d == k["ascension"]: return ("Ascension de N.S.J.C.", 1, "pascal")
        if d == k["pentecote"]: return ("Dimanche de Pentecôte", 1, "pascal")
        if dim:
            n = i // 7 + 1
            if n == 2: return ("Dimanche in albis (2e de Pâques)", 1, "pascal")
            return (f"{n}e dimanche après Pâques", 2, "pascal")
        if d == k["pentecote"] - timedelta(days=50 - 50) or False:
            pass
        return (f"{nj} du temps pascal", 4, "pascal")

    # --- Après la Pentecôte ---
    if k["pentecote"] < d < k["avent1"]:
        if d == k["trinite"]:     return ("Sainte Trinité", 1, "pentecote")
        if d == k["corpus"]:      return ("Corpus Christi", 1, "pentecote")
        if d == k["sacre_coeur"]: return ("Sacré-Cœur de Jésus", 1, "pentecote")
        if d == k["christ_roi"]:  return ("Christ-Roi", 1, "pentecote")
        if d <= k["pentecote"] + timedelta(days=6):
            return (f"{nj} dans l'octave de Pentecôte", 1, "pentecote")
        n = (d - k["pentecote"]).days // 7
        if dim:
            return (f"{n}e dimanche après la Pentecôte", 2, "pentecote")
        return (f"{nj} de la {n}e semaine après la Pentecôte", 4, "pentecote")

    return ("Férie", 4, "ordinaire")

# ======================================================================
# SANCTORAL ET PRÉSÉANCE
# ======================================================================

def sanctoral(d):
    """Sanctoral du jour, avec ajustements spéciaux."""
    # Pas de 29 fév. -> pas de règle particulière ici
    if (d.month, d.day) in SANCTORAL:
        return SANCTORAL[(d.month, d.day)]
    return None

def celebration_naturelle(d):
    """Célébration du jour AVANT application des transferts."""
    t_nom, t_cl, t_cat = temporal(d)
    s = sanctoral(d)

    # Cas particuliers : temps pascal, Noël etc. : certaines fêtes tombent dans l'octave
    if s is None:
        return (t_nom, t_cl, "", False)

    s_nom, s_cl, s_flags = s
    dim = d.isoweekday() == 7

    # Dimanche
    if dim:
        if t_cl == 1:
            return (t_nom, 1, "", False)
        if s_cl == 1:
            return (s_nom, 1, "", False)
        if s_cl == 2 and "seigneur" in s_flags:
            return (s_nom, 2, "", False)
        return (t_nom, t_cl, "", False)

    # Semaine : classe la plus haute l'emporte, sanctoral à classe égale
    if t_cl < s_cl:
        return (t_nom, t_cl, "", True) if s_cl == 1 else (t_nom, t_cl, "", False)
    if t_cl > s_cl:
        return (s_nom, s_cl, "", False)
    return (s_nom, s_cl, f"(temporal : {t_nom})", False)

def fete_empechee(d):
    """Retourne la fête de classe I du sanctoral empêchée ce jour, ou None."""
    s = sanctoral(d)
    if not s or s[1] != 1:
        return None
    nom, cl, flags = s
    if "dim_I" in flags and d.isoweekday() == 7:
        return None
    t_nom, t_cl, t_cat = temporal(d)
    if t_cl == 1 and t_nom != nom:
        return s
    if d.isoweekday() == 7 and t_cat == "avent":
        return s                                   # dimanche de l'Avent
    return None

def premier_jour_libre(d):
    x = d + timedelta(days=1)
    while True:
        t_nom, t_cl, _ = temporal(x)
        s = sanctoral(x)
        libre = t_cl > 1 and not (s and s[1] <= 2)
        if libre:
            return x
        x += timedelta(days=1)

def transferts_vers(d):
    """Cherche une fête de classe I transférée tombant le jour d."""
    for delta in range(1, 40):
        origine = d - timedelta(days=delta)
        f = fete_empechee(origine)
        if f and premier_jour_libre(origine) == d:
            return (f[0], origine)
    return None

def celebration(d):
    """Retourne (nom, classe, note)."""
    tr = transferts_vers(d)
    if tr:
        return (tr[0], 1, f"transférée du {tr[1].strftime('%d/%m')}")
    nom, cl, note, _ = celebration_naturelle(d)
    return (nom, cl, note)

# ======================================================================
# AFFICHAGE
# ======================================================================

def afficher(d):
    nom, cl, note = celebration(d)
    print(f"{JOURS[d.isoweekday()-1]:9} {d.isoformat()} | classe {ROMAIN[cl]:3} | {nom} {note}")

def annee_entiere(a):
    d = date(a, 1, 1)
    while d.year == a:
        afficher(d)
        d += timedelta(days=1)


        
ABREV = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def fichier_sancti(d):
    return f"Sancti/{d.month:02d}-{d.day:02d}"

def fichier_temporal(d):
    """Nom du fichier Tempora/ pour la date d (convention Divinum Officium)."""
    a = d.year
    k = dates_cles(a)
    p = k["paques"]
    wd = d.isoweekday() % 7            # 0 = dimanche

    # Avent
    if k["avent1"] <= d <= date(a, 12, 24):
        n = (d - k["avent1"]).days // 7 + 1
        return f"Tempora/Adv{n}-{wd}"

    # Octave de Noël et jours avant l'Épiphanie.
    # Nat25, Nat01, Nat06 n'existent pas : ces jours sont dans Sancti/.
    if d.month == 12 and d.day >= 26:
        return f"Tempora/Nat{d.day:02d}"
    if d.month == 1 and 2 <= d.day <= 5:
        return f"Tempora/Nat{d.day:02d}"
    if (d.month, d.day) in [(12, 25), (1, 1), (1, 6)]:
        return fichier_sancti(d)

    # Après l'Épiphanie
    if d < k["septuagesime"]:
        n = (d - date(a, 1, 6)).days // 7 + 1
        return f"Tempora/Epi{n}-{wd}"

    # Septuagésime
    if d < k["cendres"]:
        n = (d - k["septuagesime"]).days // 7 + 1
        return f"Tempora/Quadp{n}-{wd}"

    # Cendres et jours suivants (mercredi à samedi)
    if d < k["cendres"] + timedelta(days=4):
        return f"Tempora/Quadp3-{wd}"

    # Carême
    if d < k["rameaux"]:
        n = (d - (k["cendres"] + timedelta(days=4))).days // 7 + 1
        return f"Tempora/Quad{n}-{wd}"

    # Semaine Sainte
    if d < p:
        return f"Tempora/Quad6-{wd}"

    # Temps pascal
    if d <= k["pentecote"]:
        n = (d - p).days // 7
        return f"Tempora/Pasc{n}-{wd}"

    # Après la Pentecôte
    n = (d - k["pentecote"]).days // 7
    if n == 0:
        return f"Tempora/Pasc7-{wd}"
    reste = (k["avent1"] - d).days // 7        # semaines avant l'Avent
    if reste == 0:
        return f"Tempora/Pent24-{wd}"          # dernière semaine : toujours la 24e
    if n > 23:
        return f"Tempora/Pent{24 - reste:02d}-{wd}"   # compte à rebours
    return f"Tempora/Pent{n:02d}-{wd}"

def fichiers_du_jour(d):
    """Liste ordonnée des fichiers à consulter, par priorité."""
    nom, cl, note = celebration(d)
    tr = transferts_vers(d)
    s = sanctoral(d)
    tem = fichier_temporal(d)
    fichiers = []
    if tr:
        o = tr[1]
        fichiers.append(fichier_sancti(o))      # fête transférée
    elif s and s[0] == nom:
        fichiers.append(fichier_sancti(d))      # le saint l'emporte
    fichiers.append(tem)                         # sinon le temporal
    return fichiers


def verifier(annee):
    """Retourne la liste triée des fichiers manquants pour l'année donnée."""
    manquants = set()
    d = date(annee, 1, 1)
    while d.year == annee:
        for f in fichiers_du_jour(d):
            if not (Path("data/missa/Latin") / f"{f}.txt").exists():
                manquants.add(f)
        d += timedelta(days=1)
    return sorted(manquants)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # démo
        for jour in [date(2026, 10, 23), date(2026, 10, 24), date(2026, 12, 8),
                     date(2024, 12, 8), date(2026, 4, 5), date(2026, 12, 25)]:
            afficher(jour)
    elif sys.argv[1] == "verif":
        annees = [int(x) for x in sys.argv[2:]] or [date.today().year]
        for a in annees:
            print(a, verifier(a))
    elif len(sys.argv[1]) == 4:
        annee_entiere(int(sys.argv[1]))
    else:
        y, m, j = map(int, sys.argv[1].split("-"))
        afficher(date(y, m, j))
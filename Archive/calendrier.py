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

# ----------------------------------------------------------------------
# Données de propres provenant du CSV « proper of saints.csv » (jgabc).
# Enregistrements: mois, jour, date CSV, fête, puis les incipits du propre.
PROPER_OF_SAINTS = [(1, 5, 'Jan 5', 'St Telesphorus', 'puer natus est', 'viderunt omnes', '', 'multifarie olim', '', 'tui sunt caeli', 'viderunt omnes'), (1, 11, 'Jan 11', 'St Hyginus', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (1, 13, 'Jan 13', 'Baptism of Our Lord Jesus Christ', 'ecce advenit', 'omnes de saba', '', 'vidimus stellam', '', 'reges tharsis', 'vidimus stellam'), (1, 14, 'Jan 14', 'St Hilary', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (1, 15, 'Jan 15', 'St Paul the First Hermit', 'justus ut palma', 'justus ut palma', '', 'justus germinabit', '', 'in virtute tua', 'laetabitur justus'), (1, 16, 'Jan 16', 'St Marcellus I', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (1, 17, 'Jan 17', 'St Anthony', 'os justi', 'domine praevenisti', '', 'justus ut palma', '', 'desiderium animae', 'fidelis servus'), (1, 18, 'Jan 18', 'Chair of St Peter in Rome', 'statuit', 'exaltent eum', 'tu es petrus', 'tu es petrus', '', 'tu es petrus', 'tu es petrus'), (1, 20, 'Jan 20', 'St Fabian and St Sebastian', 'intret in conspectu', 'gloriosus deus', 'qui seminant', 'sancti tui... benedicent', '', 'laetamini', 'multitudo languentium'), (1, 21, 'Jan 21', 'St Agnes', 'me exspectaverunt', 'diffusa est', 'veni sponsa', 'quinque prudentes', '', 'afferentur... proximae', 'quinque prudentes'), (1, 22, 'Jan 22', 'Ss Vincent and Anastasius', 'intret in conspectu', 'gloriosus deus', 'qui seminant', 'corpora sanctorum', '', 'mirabilis deus', 'et si coram'), (1, 23, 'Jan 23', 'St Raymond of Penafort', 'os justi', 'justus ut palma', 'beatus vir qui timet', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (1, 24, 'Jan 24', 'St Timothy', 'statuit', 'inveni david', 'desiderium', 'tu es sacerdos', '', 'veritas mea', 'semel juravi'), (1, 25, 'Jan 25', 'Conversion of St Paul', 'scio cui credidi', 'qui operatus est', 'tu es vas', 'magnus sanctus paulus', '', 'mihi autem nimis', 'amen dico vobis quod vos'), (1, 26, 'Jan 26', 'St Polycarp', 'sacerdotes dei', 'ecce sacerdos', 'beatus vir qui timet', 'hic est sacerdos', '', 'inveni david', 'posuisti domine'), (1, 27, 'Jan 27', 'St John Chrysostom', 'in medio', 'ecce sacerdos', 'beatus vir qui timet', 'beatus vir qui suffert', '', 'justus ut palma', 'fidelis servus'), (1, 28, 'Jan 28', 'St Peter Nolasco', 'justus ut palma', 'os justi', 'beatus vir qui timet', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (1, 29, 'Jan 29', 'St Francis de Sales', 'in medio', 'os justi', 'beatus vir qui timet', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (1, 30, 'Jan 30', 'St Martina', 'loquebar ps. beati immaculati', 'dilexisti', 'veni sponsa', 'adducentur', '', 'afferentur... proximae', 'confundantur'), (1, 31, 'Jan 31', 'St John Bosco', 'dedit illi', 'spera', 'factus es', 'pauper', '', 'venite filii', 'contra spem'), (2, 1, 'Feb 1', 'St Ignatius', 'mihi autem absit ps. memento', 'ecce sacerdos', 'desiderium', 'christo confixus', '', 'gloria et honore', 'frumentum'), (2, 2, 'Feb 2', 'Purification of BVM', 'suscepimus', 'suscepimus deus', 'nunc dimittis', 'senex puerum', '', 'diffusa est', 'responsum'), (2, 3, 'Feb 3', 'St Blase', 'sacerdotes dei', 'gloria et honore', 'beatus vir qui timet', 'hic est sacerdos', '', 'inveni david', 'posuisti domine'), (2, 4, 'Feb 4', 'St Andrew Corsini', 'statuit', 'ecce sacerdos', 'beatus vir qui timet', 'tu es sacerdos', '', 'inveni david', 'fedelis servus'), (2, 5, 'Feb 5', 'St Agatha', 'gaudeamus... agathae', 'adjuvabit eam', 'qui seminant', 'loquebar', '', 'afferentur... proximae', 'qui me dignatus est'), (2, 6, 'Feb 6', 'St Titus', 'statuit', 'ecce sacerdos', 'beatus vir qui timet', 'tu es sacerdos', '', 'inveni david', 'fedelis servus'), (2, 7, 'Feb 7', 'St Romuald', 'os justi', 'domine praevenisti', 'beatus vir qui timet', 'justus ut palma', '', 'desiderium animae', 'fidelis servus'), (2, 8, 'Feb 8', 'St John of Matha', 'os justi', 'justus ut palma', 'beatus vir qui timet', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (2, 9, 'Feb 9', 'St Cyril of Alexandria', 'in medio', 'os justi', 'beatus vir qui timet', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (2, 10, 'Feb 10', 'St Scholastica', 'dilexisti', 'specie tua', 'audi filia', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (2, 11, 'Feb 11', 'Apparition of BVM at Lourdes', 'vidi civitatem', 'flores apparuerunt', 'tu gloria jerusalem', 'ostende mihi', '', 'ave gratia plena', 'visitasti terram'), (2, 12, 'Feb 12', 'Seven Founders of the Servite Order', 'justi decantaverunt', 'electi mei', 'qui seminant', 'sapientiam', '', 'adducam eos', 'ego vos elegi'), (2, 14, 'Feb 14', 'St Valentine', 'in virtute tua', 'beatus vir qui timet', 'desiderium', 'posuisti domine', '', 'gloria et honore', 'qui vult venire'), (2, 15, 'Feb 15', 'Ss Faustinus and Jovita', 'salus autem', 'clamaverunt', 'qui seminant', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (2, 18, 'Feb 18', 'St Simeon', 'statuit', 'inveni david', 'desiderium', 'tu es sacerdos', '', 'veritas mea', 'semel juravi'), (2, 22, 'Feb 22', 'Chair of St Peter', 'statuit', 'exaltent eum', 'tu es petrus', 'tu es petrus', '', 'tu es petrus', 'tu es petrus'), (2, 23, 'Feb 23', 'St Peter Damian', 'in medio', 'os justi', 'beatus vir qui timet', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (2, 24, 'Feb 24 or 25', 'St Matthias', 'mihi autem nimis', 'nimis honorati', 'desiderium', '', '', 'constitues eos', 'vos qui secuti'), (2, 27, 'Feb 27 or 28', 'St Gabriel of Our Lady of Sorrows', 'oculus dei', 'quam magna', 'beatus vir cujus', 'minuisti eum', '', 'o domine... et filius', 'ecce sto'), (3, 4, 'Mar 4', 'St Casimir of Lithuania', 'os justi', 'justus ut palma', 'beatus vir qui timet', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (3, 6, 'Mar 6', 'Ss Perpetua and Felicity and Companions', 'me exspectaverunt', 'dilexisti', 'veni sponsa', '', '', 'diffusa est', 'principes'), (3, 7, 'Mar 7', 'St Thomas Aquinas', 'in medio', 'os justi', 'beatus vir qui timet', '', '', 'justus ut palma', 'fidelis servus'), (3, 8, 'Mar 8', 'St John of God', 'os justi', 'justus ut palma', 'beatus vir qui timet', '', '', 'veritas mea', 'beatus servus'), (3, 9, 'Mar 9', 'St Frances of Rome', 'cognovi', 'diffusa est', 'veni sponsa', '', '', 'diffusa est', 'dilexisti'), (3, 10, 'Mar 10', 'Forty Martyrs of Sebaste', 'clamaverunt justi', 'ecce quam bonum', 'qui seminant', '', '', 'laetamini', 'quicumque fecerit'), (3, 12, 'Mar 12', 'St Gregory the Great', 'si diligis me', 'exaltent eum', 'annuntiavi', '', '', 'ecce dedi', 'tu es petrus'), (3, 17, 'Mar 17', 'St Patrick', 'statuit', 'ecce sacerdos', 'beatus vir qui timet', '', '', 'inveni david', 'fidelis servus'), (3, 18, 'Mar 18', 'St Cyril of Jerusalem', 'in medio', 'os justi', 'beatus vir qui timet', '', '', 'justus ut palma', 'fidelis servus'), (3, 19, 'Mar 19', 'St Joseph', 'justus ut palma', 'domine praevenisti', 'beatus vir qui timet', 'amavit eum', 'justus germinabit', 'veritas mea', 'joseph fili david'), (3, 21, 'Mar 21', 'St Benedict', 'os justi', 'domine praevenisti', 'beatus vir qui timet', '', '', 'desiderium animae', 'fidelis servus'), (3, 24, 'Mar 24', 'St Gabriel the Archangel', 'benedicite dominum', 'benedicite dominum', 'ave maria', '', '', 'stetit angelus', 'benedicite omnes angeli'), (3, 25, 'Mar 25', 'Annunciation of Our Lady', 'vultum tuum', 'diffusa est', 'audi filia', 'ave maria', 'virga jesse', 'ave maria... et benedictus', 'ecce virgo'), (3, 27, 'Mar 27', 'St John Damascene', 'tenuisti manum', 'deus qui praecinxit me', 'persequar', '', '', 'lignum habet', 'brachia peccatorum'), (3, 28, 'Mar 28', 'St John Capistran', 'ego autem in... gaudebo', 'qui timetis', 'fortitudo mea', '', '', 'invocavit', 'decantaverunt'), (4, 2, 'Apr 2', 'St Francis of Paula', 'justus ut palma', 'os justi', 'beatus vir qui timet', 'beatus vir qui timet', 'justus germinabit', 'in virtute tua', 'amen dico vobis quod vos'), (4, 4, 'Apr 4', 'St Isidore', 'in medio', 'os justi', 'beatus vir qui timet', 'amavit eum', 'justus germinabit', 'justus ut palma', 'fidelis servus'), (4, 5, 'Apr 5', 'St Vincent Ferrer', 'os justi', 'justus ut palma', 'beatus vir qui timet', 'beatus vir qui timet', 'amavit eum', 'veritas mea', 'beatus servus'), (4, 11, 'Apr 11', 'St Leo I', 'si diligis me', 'exaltent eum', 'annuntiavi', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus'), (4, 13, 'Apr 13', 'St Hermenegild', 'protexisti me', 'inveni david', 'desiderium', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (4, 14, 'Apr 14', 'St Justin', 'narraverunt', '', '', 'sapientia hujus', 'verumtamen', 'non enim judicavi', 'reposita est'), (4, 17, 'Apr 17', 'St Anicetus', 'si diligis me', 'exaltent eum', 'annuntiate', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus'), (4, 21, 'Apr 21', 'St Anselm', 'in medio', 'os justi', '', 'amavit eum', 'justus germinabit', 'justus ut palma', 'fidelis servus'), (4, 22, 'Apr 22', 'Ss Soter and Caius', 'si diligis me', 'exaltent eum', '', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus'), (4, 23, 'Apr 23', 'St George', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (4, 24, 'Apr 24', 'St Fidelis of Sigmaringen', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (4, 25, 'Apr 25', 'St Mark', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (4, 26, 'Apr 26', 'Ss Cletus and Marcellinus', 'si diligis me', 'exaltent eum', 'annuntiavi', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus'), (4, 27, 'Apr 27', 'St Peter Canisius', 'in medio', 'os justi', '', 'amavit eum', 'justus germinabit', 'justus ut palma', 'fidelis servus'), (4, 28, 'Apr 28', 'St Paul of the Cross', 'christo confixus sum', '', '', 'pro omnibus', 'si filii', 'ambulate', 'communicantes'), (4, 29, 'Apr 29', 'St Peter of Verona', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (4, 30, 'Apr 30', 'St Catherine of Sienna', 'dilexisti', '', '', 'adducentur', 'specie tua', 'filiae regum', 'quinque prudentes'), (5, 1, 'May 1', 'St Joseph the Worker', 'sapientia reddidit', 'beatus quicumque', '', 'de quacumque', 'fac nos innocuam', 'bonitas domini', 'unde huic sapientia haec'), (5, 2, 'May 2', 'St Athanasius', 'in medio', '', '', 'tu es sacerdos', 'beatus vir qui suffert', 'inveni david', 'quod dico vobis'), (5, 4, 'May 4', 'St Monica', 'cognovi', '', '', 'specie tua', 'propter veritatem', 'diffusa est', 'dilexisti'), (5, 5, 'May 5', 'St Pius V', 'si diligis me', 'exaltent eum', '', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus... alleluia'), (5, 7, 'May 7', 'St Stanislaus', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (5, 9, 'May 9', 'St Gregory Nazianzen', 'in medio', 'os justi', '', 'amavit eum', 'justus germinabit', 'justus ut palma', 'fidelis servus'), (5, 10, 'May 10', 'St Antoninus', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (5, 11, 'May 11', 'Ss Philip and James', 'exclamaverunt', '', '', 'confitebuntur', 'tanto tempore', 'confitebuntur', 'tanto tempore'), (5, 12, 'May 12', 'Ss Nereus, Achilleus, Domitilla, and Pancras', 'ecce oculi', '', '', 'haec est vera', 'te martyrum', 'confitebuntur', 'gaudete cum alleluia'), (5, 13, 'May 13', 'St Robert Bellarmine', 'in medio', '', '', 'qui docti fuerint', 'qui ad justitiam', 'mihi autem adhaerere', 'vos estis lux'), (5, 15, 'May 15', 'St John Baptist de la Salle', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', 'amavit eum', 'veritas mea', 'beatus servus'), (5, 16, 'May 16', 'St Ubaldus', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', 'hic est sacerdos', 'inveni david', 'fidelis servus'), (5, 17, 'May 17', 'St Paschal Baylon', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', 'amavit eum', 'veritas mea', 'beatus servus'), (5, 18, 'May 18', 'St Venantius', 'protexisti me', '', '', 'confitebuntur', 'posuisti domine', 'confitebuntur', 'laetabitur justus'), (5, 19, 'May 19', 'St Peter Celestine', 'si diligis me', 'exaltent eum', '', 'tu es petrus', 'constitues eos', 'ecce dedi', 'tu es petrus... alleluia'), (5, 20, 'May 20', 'St Bernardine of Siena', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', 'amavit eum', 'veritas mea', 'beatus servus'), (5, 24, 'May 24', 'Our Lady Help of Christians', 'salve sancta parens', 'benedicta et venerabilis', '', 'post partum', '', 'ave maria... et benedictus', 'beata viscera'), (5, 26, 'May 26', 'St Philip Neri', 'caritas dei sine alleluia', 'venite filii', '', 'de excelso', 'concaluit cor', 'viam mandatorum', 'cor meum'), (5, 27, 'May 27', 'St Bede the Venerable', 'in medio', 'os justi', '', 'amavit eum', 'justus germinabit', 'justus ut palma', 'fidelis servus'), (5, 28, 'May 28', 'St Augustine of Canterbury', 'sacerdotes tui', 'sacerdotes ejus', '', 'juravit dominus', 'amavit eum', 'veritas mea', 'beatus servus'), (5, 29, 'May 29', 'St Mary Magdalen of Pazzi', 'dilexisti', 'specie tua', '', 'adducentur', 'specie tua', 'filiae regum', 'quinque prudentes'), (5, 30, 'May 30', 'St Felix', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (5, 31, 'May 31', 'Queenship of BVM', 'gaudeamus... mariae... solemnitate', 'ipse habet', '', 'salve regina', 'nunc cum eo', 'regali ex progenie', 'regina mundi'), (6, 1, 'Jun 1', 'St Angela Merici', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (6, 4, 'Jun 4', 'St Francis Caracciolo', 'factum est', 'quemadmodum', '', 'defecit caro', '', 'justus ut palma', 'quam magna'), (6, 5, 'Jun 5', 'St Boniface', 'exsultabo in jerusalem', 'communicantes', '', 'declinabo', '', 'benedicam dominum', 'qui vicerit'), (6, 6, 'Jun 6', 'St Norbert', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (6, 10, 'Jun 10', 'St Margaret', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (6, 11, 'Jun 11', 'St Barnabas', 'mihi autem nimis', 'in omnem terram', '', 'ego vos elegi', '', 'constitues eos', 'vos qui secuti'), (6, 12, 'Jun 12', 'St John of San Facundo', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (6, 13, 'Jun 13', 'St Anthony of Padua', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (6, 14, 'Jun 14', 'St Basil the Great', 'in medio', 'os justi', '', 'inveni david', '', 'veritas mea', 'fidelis servus'), (6, 17, 'Jun 17', 'St Gregory Barbadici', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (6, 18, 'Jun 18', 'St Ephrem', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (6, 19, 'Jun 19', 'St Juliana Falconieri', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (6, 20, 'Jun 20', 'St Silverius', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (6, 21, 'Jun 21', 'St Aloysius Gonzaga', 'minuisti eum', 'domine spes mea', '', 'beatus quem elegisti', '', 'quis ascendet', 'panem caeli'), (6, 22, 'Jun 22', 'St Paulinus', 'sacerdotes tui', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (6, 24, 'Jun 24', 'Birth of St John the Baptist', 'de ventre matris', 'priusquam', '', 'tu puer', '', 'justus ut palma', 'tu puer'), (6, 25, 'Jun 25', 'St William', 'os justi', 'domine praevenisti', '', 'justus ut palma', '', 'desiderium animae', 'fidelis servus'), (6, 26, 'Jun 26', 'Ss John and Paul', 'multae tribulationes', 'ecce quam bonum', '', 'haec est vera', '', 'gloriabuntur', 'et si coram'), (6, 29, 'Jun 29', 'Ss Peter and Paul', 'nunc scio vere', 'constitues eos', '', 'tu es petrus', '', 'constitues eos', 'tu es petrus'), (6, 30, 'Jun 30', 'Commemoration of St Paul', 'scio cui credidi', 'qui operatus est', '', 'sancte paule', '', 'mihi autem nimis', 'amen dico vobis quod vos'), (7, 1, 'Jul 1', 'The Most Precious Blood of Our Lord', 'redemisti nos', 'hic est qui venit', '', 'si testimonium', '', 'calix benedictionis', 'christus semel'), (7, 2, 'Jul 2', 'The Visitation of BVM', 'salve sancta parens', 'benedicta et venerabilis', '', 'felix es sacra', '', 'beata es virgo', 'beata viscera'), (7, 3, 'Jul 3', 'St Irenaeus', 'lex veritatis', 'propter fratres meos', '', 'in multitudine', '', 'doctrinam', 'videte'), (7, 5, 'Jul 5', 'St Anthony Mary Zaccaria', 'sermo meus', 'testis mihi', '', 'repleti fructu', '', 'in conspectu angelorum', 'imitatores'), (7, 7, 'Jul 7', 'Ss Cyril and Methodius', 'sacerdotes tui', 'sacerdotes ejus', '', 'juravit dominus', '', 'mirabilis deus', 'quod dico vobis'), (7, 8, 'Jul 8', 'St Elizabeth', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (7, 10, 'Jul 10', 'The Seven Holy Brothers', 'laudate pueri', 'anima... sicut passer', '', 'haec est vera', '', 'anima nostra', 'quicumque fecerit'), (7, 11, 'Jul 11', 'St Oliver Plunkett', 'statuit', 'inveni david', '', 'tu es sacerdos', '', 'veritas mea', 'semel juravi'), (7, 12, 'Jul 12', 'St John Gualbert', 'os justi', 'domine praevenisti', '', 'justus ut palma', '', 'desiderium animae', 'fidelis servus'), (7, 14, 'Jul 14', 'St Bonaventure', 'in medio', 'os justi', '', 'juravit dominus', '', 'veritas mea', 'fidelis servus'), (7, 15, 'Jul 15', 'St Henry', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (7, 16, 'Jul 16', 'Our Lady of Mount Carmel', 'gaudeamus... mariae... assumptione', 'benedicta et venerabilis', '', 'per te dei genitrix', '', 'recordare virgo', 'regina mundi'), (7, 17, 'Jul 17', 'St Alexius', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (7, 18, 'Jul 18', 'St Camillus de Lellis', 'majorem', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'infirmus fui'), (7, 19, 'Jul 19', 'St Vincent de Paul', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (7, 20, 'Jul 20', 'St Jerome Emilian', 'effusum est', 'deriventur', '', 'dispersit', '', 'quando orabas', 'religio munda'), (7, 21, 'Jul 21', 'St Lawrence of Brindisi', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (7, 22, 'Jul 22', 'St Mary Magdalen', 'me exspectaverunt', 'dilexisti', '', 'diffusa est', '', 'filiae regum', 'feci judicium'), (7, 23, 'Jul 23', 'St Apollinaris', 'sacerdotes dei', 'inveni david', '', 'juravit dominus', '', 'veritas mea', 'domine quinque talenta'), (7, 25, 'Jul 25', 'St James the Greater', 'mihi autem nimis', 'constitues eos', '', 'ego vos elegi', '', 'in omnem terram', 'vos qui secuti'), (7, 26, 'Jul 26', 'St Anne', 'gaudeamus... annae', 'dilexisti', '', 'diffusa est', '', 'filiae regum', 'diffusa'), (7, 27, 'Jul 27', 'St Pantaleon', 'laetabitur justus', 'justus cum ceciderit', '', 'qui sequitur me', '', 'posuisti', 'qui mihi ministrat'), (7, 28, 'Jul 28', 'Ss Nazarius and Celsus', 'intret in conspectu', 'gloriosus deus', '', 'corpora sanctorum', '', 'mirabilis deus', 'et si coram'), (7, 29, 'Jul 29', 'St Martha', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (7, 31, 'Jul 31', 'St Ignatius of Loyola', 'in nomine jesu ps. gloriabuntur', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'ignem veni'), (8, 1, 'Aug 1', 'Holy Machabees', 'clamaverunt justi', 'ecce quam bonum', '', 'haec est vera', '', 'exsultabunt sancti', 'dico autem vobis'), (8, 2, 'Aug 2', 'St Alphonsus Mary de Ligouri', 'spiritus domini super me', 'memor fui', '', 'ipse est directus', '', 'honora dominum', 'sacerdos magnus'), (8, 4, 'Aug 4', 'St Dominic', 'os justi', 'justus ut palma', '', 'justus germinabit', '', 'veritas mea', 'fidelis servus'), (8, 5, 'Aug 5', 'Dedication of the Basilica of St Mary Major', 'salve sancta parens', 'benedicta et venerabilis', '', 'post partum', '', 'ave maria... et benedictus', 'beata viscera'), (8, 6, 'Aug 6', 'Transfiguration of Our Lord', 'illuxerunt', 'speciosus. ℣. eructavit', '', 'candor est', '', 'gloria et divitiae', 'visionem'), (8, 7, 'Aug 7', 'St Cajetan', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (8, 8, 'Aug 8', 'St John Mary Vianney', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (8, 10, 'Aug 10', 'St Lawrence', 'confessio', 'probasti domine', '', 'levita laurentius', '', 'confessio', 'qui mihi ministrat'), (8, 11, 'Aug 11', 'St Tiburtius and St Susanna', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (8, 12, 'Aug 12', 'St Clare', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (8, 13, 'Aug 13', 'Ss Hippolytus and Cassian', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (8, 15, 'Aug 15', 'Assumption of BVM', 'signum magnum', 'audi filia... et concupiscet', '', 'assumpta est', '', 'inimicitias ponam', 'beatam me dicent'), (8, 16, 'Aug 16', 'St Joachim', 'dispersit', 'dispersit', '', 'o joachim', '', 'gloria et honore', 'fidelis servus'), (8, 17, 'Aug 17', 'St Hyacinth', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (8, 18, 'Aug 18', 'St Agapitus', 'laetabitur justus', 'justus cum ceciderit', '', 'qui sequitur me', '', 'posuisti', 'qui mihi ministrat'), (8, 19, 'Aug 19', 'St John Eudes', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (8, 20, 'Aug 20', 'St Bernard', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (8, 21, 'Aug 21', 'St Jane Frances de Chantal', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (8, 22, 'Aug 22', 'Feast of the Immaculate Heart of BVM', 'adeamus ps. eructavit', 'exsultabit', '', 'magnificat', '', 'exsultavit', 'dixit jesus'), (8, 23, 'Aug 23', 'St Philip Benizi', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (8, 24, 'Aug 24', 'St Bartholomew', 'mihi autem nimis', 'constitues eos', '', 'te gloriosus', '', 'mihi autem nimis', 'vos qui secuti... dicit'), (8, 25, 'Aug 25', 'St Louis', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (8, 27, 'Aug 27', 'St Joseph Calasanctius', 'venite filii', 'os justi', '', 'beatus vir qui suffert', '', 'desiderium pauperum', 'sinite parvulos'), (8, 28, 'Aug 28', 'St Augustine', 'in medio', 'os justi', '', 'inveni david', '', 'justus ut palma', 'fidelis servus'), (8, 29, 'Aug 29', 'Beheading of St John the Baptist', 'loquebar ps. bonum est', 'justus ut palma', '', 'justus germinabit', '', 'in virtute tua', 'posuisti domine'), (8, 30, 'Aug 30', 'St Rose of Lima', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (8, 31, 'Aug 31', 'St Raymund Nonnatus', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (9, 2, 'Sep 2', 'St Stephen', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (9, 3, 'Sep 3', 'St Pius X', 'extuli electum', 'annuntiavi justitiam', 'sacerdotes ejus', 'paras mihi mensam', 'domine diligo', 'venite filii', 'caro mea'), (9, 5, 'Sep 5', 'St Lawrence Justinian', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (9, 8, 'Sep 8', 'Nativity of BVM', 'salve sancta parens', 'benedicta et venerabilis', '', 'felix es sacra', '', 'beata es virgo', 'beata viscera'), (9, 9, 'Sep 9', 'St Gorgonius', 'laetabitur justus', 'justus cum ceciderit', '', 'qui sequitur me', '', 'posuisti', 'qui mihi ministrat'), (9, 10, 'Sep 10', 'St Nicholas of Tolentino', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (9, 11, 'Sep 11', 'Ss Protus and Hyacinth', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (9, 12, 'Sep 12', 'Most Holy Name of Mary', 'vultum tuum', 'benedicta et venerabilis', '', 'post partum', '', 'ave maria... et benedictus', 'beata viscera'), (9, 14, 'Sep 14', 'The Exaltation of the Holy Cross', 'nos autem', 'christus factus est', '', 'dulce lignum', '', 'protege domine', 'per signum crucis'), (9, 15, 'Sep 15', 'Seven Sorrows of BVM', 'stabant', 'dolorosa', '', 'stabat sancta maria', '', 'recordare virgo', 'felices sensus'), (9, 16, 'Sep 16', 'St Cornelius', 'intret in conspectu', 'gloriosus deus', '', 'corpora sanctorum', '', 'mirabilis deus', 'et si coram'), (9, 17, 'Sep 17', 'The Stigmata of St Francis', 'mihi autem absit ps. voce', 'os justi', '', 'franciscus', '', 'veritas mea', 'fidelis servus'), (9, 18, 'Sep 18', 'St Joseph of Cupertino', 'dilectio dei', 'domine praevenisti', '', 'oculus dei', '', 'ego autem', 'ego sum pauper'), (9, 19, 'Sep 19', 'St Januarius', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (9, 21, 'Sep 21', 'St Matthew', 'os justi', 'beatus vir qui timet', '', 'te gloriosus', '', 'posuisti', 'magna est'), (9, 22, 'Sep 22', 'St Thomas of Villanova', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (9, 23, 'Sep 23', 'St Linus', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (9, 24, 'Sep 24', 'Our Lady of Ransom', 'salve sancta parens', 'benedicta et venerabilis', '', 'post partum', '', 'ave maria... et benedictus', 'beata viscera'), (9, 26, 'Sep 26', 'Ss Cyprian and Justina', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (9, 27, 'Sep 27', 'Ss Cosmas and Damian', 'sapientiam sanctorum', 'clamaverunt', '', 'haec est vera', '', 'gloriabuntur', 'posuerunt'), (9, 28, 'Sep 28', 'St Wenceslaus', 'in virtute tua', 'beatus vir qui timet', '', 'posuisti domine', '', 'gloria et honore', 'qui vult venire'), (9, 29, 'Sep 29', 'St Michael the Archangel ', 'benedicite dominum', 'benedicite dominum', '', 'sancte michael', '', 'stetit angelus', 'benedicite omnes angeli'), (9, 30, 'Sep 30', 'St Jerome', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (10, 2, 'Oct 2', 'The Holy Guardian Angels', 'benedicite dominum', 'angelis suis', '', 'benedicite domino', '', 'benedicite dominum', 'benedicite omnes angeli'), (10, 3, 'Oct 3', 'St Theresa of the Child Jesus', 'veni de libano', 'confiteor tibi', '', 'quasi rosa', '', 'magnificat', 'circumduxit eam'), (10, 4, 'Oct 4', 'St Francis of Assisi', 'mihi autem absit ps. voce', 'os justi', '', 'franciscus', '', 'veritas mea', 'fidelis servus'), (10, 5, 'Oct 5', 'St Placid and Companions', 'salus autem', 'clamaverunt', '', 'te martyrum', '', 'justorum animae', 'quod dico vobis'), (10, 6, 'Oct 6', 'St Bruno', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (10, 7, 'Oct 7', 'The Most Holy Rosary of BVM', 'gaudeamus... mariae... solemnitate', 'propter veritatem', '', 'solemnitas', '', 'in me gratia', 'florete... et date'), (10, 8, 'Oct 8', 'St Bridget', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (10, 9, 'Oct 9', 'St John Leonardi', 'in sermonibus', 'inflammatum est', '', 'tamquam prodigium', '', 'christi factus sum', 'quae mihi fuerunt'), (10, 10, 'Oct 10', 'St Francis Borgia', 'os justi', 'domine praevenisti', '', 'justus ut palma', '', 'desiderium animae', 'fidelis servus'), (10, 11, 'Oct 11', 'The Motherhood of BVM', 'ecce virgo', 'egredietur virga', '', 'virgo dei genitrix', '', 'cum esset desponsata', 'beata viscera'), (10, 13, 'Oct 13', 'St Edward', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (10, 14, 'Oct 14', 'St Callistus', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (10, 15, 'Oct 15', 'St Teresa of Avila', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (10, 16, 'Oct 16', 'St Hedwig', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (10, 17, 'Oct 17', 'St Margaret Mary Alacoque', 'sub umbra', 'aquae multae', '', 'ego dilecto', '', 'quid bonum', 'ego dilecto'), (10, 18, 'Oct 18', 'St Luke', 'mihi autem nimis', 'in omnem terram', '', 'ego vos elegi', '', 'mihi autem nimis', 'vos qui secuti'), (10, 19, 'Oct 19', 'St Peter of Alcantara', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (10, 20, 'Oct 20', 'St John Cantius', 'miseratio', 'confiteantur domino', '', 'manum suam', '', 'justitia indutus', 'date et dabitur'), (10, 23, 'Oct 23', 'St Anthony Mary Claret', 'sacerdotes tui', 'sacerdotes ejus', '', 'juravit dominus', '', 'veritas mea', 'beatus servus'), (10, 24, 'Oct 24', 'St Raphael', 'benedicite dominum', 'angelis domini', '', 'in conspectu... adorabo', '', 'stetit angelus', 'benedicite omnes angeli'), (10, 28, 'Oct 28', 'Ss Simon and Jude', 'mihi autem nimis', 'constitues eos', '', 'te gloriosus', '', 'in omnem terram', 'vos qui secuti'), (11, 1, 'Nov 1', 'The Feast of All Saints', 'gaudeamus... sanctorum omnium', 'timete dominum', '', 'venite ad me', '', 'justorum animae', 'beati mundo corde'), (11, 2, 'Nov 2', "All Souls' Day", 'requiem', 'requiem', 'absolve', '', '', 'domine jesu christe', 'lux aeterna'), (11, 4, 'Nov 4', 'St Charles Borromeo', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (11, 8, 'Nov 8', 'Four Holy Crowned Martyrs', 'intret in conspectu', 'gloriosus deus', '', 'sancti tui... benedicent', '', 'laetamini', 'multitudo languentium'), (11, 9, 'Nov 9', 'The Dedication of the Lateran Basilica', 'terribilis est', 'locus iste', '', 'adorabo', '', 'domine deus... qui repertus', 'domus mea'), (11, 10, 'Nov 10', 'St Andrew Avellino', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (11, 11, 'Nov 11', 'St Martin of Tours', 'statuit', 'ecce sacerdos', '', 'beatus vir sanctus martinus', '', 'veritas mea', 'beatus servus'), (11, 12, 'Nov 12', 'St Martin I', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (11, 13, 'Nov 13', 'St Didacus', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (11, 14, 'Nov 14', 'St Josaphat', 'gaudeamus... josaphat', 'inveni david', '', 'hic est sacerdos', '', 'majorem caritatem', 'ego sum pastor'), (11, 15, 'Nov 15', 'St Albert the Great', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (11, 16, 'Nov 16', 'St Gertrude', 'dilexisti', 'specie tua', '', 'adducentur', '', 'filiae regum', 'quinque prudentes'), (11, 17, 'Nov 17', 'St Gregory the Wonderworker', 'statuit', 'ecce sacerdos', '', 'tu es sacerdos', '', 'inveni david', 'fidelis servus'), (11, 18, 'Nov 18', 'The Dedication of the Basilicas of Ss Peter and Paul', 'terribilis est', 'locus iste', '', 'adorabo', '', 'domine deus... qui repertus', 'domus mea'), (11, 19, 'Nov 19', 'St Elizabeth of Hungary', 'cognovi', 'diffusa est', '', 'specie tua', '', 'diffusa est', 'dilexisti'), (11, 20, 'Nov 20', 'St Felix of Valois', 'justus ut palma', 'os justi', '', 'beatus vir qui timet', '', 'in virtute tua', 'amen dico vobis quod vos'), (11, 21, 'Nov 21', 'The Presentation of BVM', 'salve sancta parens', 'benedicta et venerabilis', '', 'post partum', '', 'ave maria', 'beata viscera'), (11, 22, 'Nov 22', 'St Cecilia', 'loquebar ps. beati immaculati', 'audi filia...quia concupivit', '', 'quinque prudentes', '', 'afferentur... proximae', 'confundantur'), (11, 23, 'Nov 23', 'St Clement I', 'dicit dominus : sermones', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (11, 24, 'Nov 24', 'St John of the Cross', 'in medio', 'os justi', '', 'amavit eum', '', 'justus ut palma', 'fidelis servus'), (11, 25, 'Nov 25', 'St Catherine of Alexandria', 'loquebar ps. beati immaculati', 'dilexisti', '', 'adducentur', '', 'afferentur... proximae', 'confundantur'), (11, 26, 'Nov 26', 'St Sylvester', 'os justi', 'domine praevenisti', '', 'justus ut palma', '', 'desiderium pauperum', 'fidelis servus'), (11, 27, 'Nov 27', 'Our Lady of the Miraculous Medal', 'erit quasi signum', 'mementote', '', 'a summo caelo', '', 'erit vobis', 'innova signa'), (11, 29, 'Nov 29', 'St Saturninus', 'laetabitur justus', 'justus cum ceciderit', '', 'qui sequitur me', '', 'posuisti', 'qui mihi ministrat'), (11, 30, 'Nov 30', 'St Andrew', 'mihi autem nimis', 'constitues eos', '', 'dilexit andream', '', 'mihi autem nimis', 'venite post me'), (12, 2, 'Dec 2', 'St Bibiana', 'me exspectaverunt', 'adjuvabit eam', '', 'haec est virgo', '', 'diffusa est', 'feci judicium'), (12, 3, 'Dec 3', 'St Francis Xavier', 'loquebar ps. laudate', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (12, 4, 'Dec 4', 'St Peter Chrysologus', 'in medio', 'ecce sacerdos', '', 'tu es sacerdos', '', 'justus ut palma', 'domine quinque talenta'), (12, 5, 'Dec 5', 'St Sabbas', 'os justi', 'justus ut palma', '', 'beatus vir qui suffert', '', 'veritas mea', 'beatus servus'), (12, 6, 'Dec 6', 'St Nicholas', 'statuit', 'inveni david', '', 'justus ut palma', '', 'veritas mea', 'semel juravi'), (12, 7, 'Dec 7', 'St Ambrose', 'in medio', 'ecce sacerdos', '', 'juravit dominus', '', 'veritas mea', 'semel juravi'), (12, 8, 'Dec 8', 'The Immaculate Conception of BVM', 'gaudens gaudebo... quasi', 'benedicta es tu', '', 'tota pulchra es', '', 'ave maria', 'gloriosa'), (12, 10, 'Dec 10', 'St Melchiades', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (12, 11, 'Dec 11', 'St Damasus', 'si diligis me', 'exaltent eum', '', 'tu es petrus', '', 'ecce dedi', 'tu es petrus'), (12, 12, 'Dec 12', 'Our Lady of Guadalupe', 'salve sancta parens', 'quae est ista', '', 'flores... tempus', '', 'elegi', 'non fecit'), (12, 13, 'Dec 13', 'St Lucy', 'dilexisti', 'dilexisti', '', 'diffusa est', '', 'afferentur... post eam', 'principes'), (12, 16, 'Dec 16', 'St Eusebius', 'sacerdotes dei', 'gloria et honore', '', 'hic est sacerdos', '', 'inveni david', 'posuisti domine'), (12, 21, 'Dec 21', 'St Thomas', 'mihi autem nimis', 'nimis honorati', '', 'gaudete justi', '', 'in omnem terram', 'mitte manum tuam'), (12, 26, 'Dec 26', 'St Stephen', 'etenim sederunt', 'sederunt principes', '', 'video caelos', '', 'elegerunt apostoli', 'video caelos'), (12, 27, 'Dec 27', 'St John', 'in medio', 'exiit sermo', '', 'hic est discipulus', '', 'justus ut palma', 'exiit sermo'), (12, 28, 'Dec 28', 'The Holy Innocents', 'ex ore infantium', 'anima... sicut passer', '', 'laudate pueri', '', 'anima nostra', 'vox in rama')]

# Complète les entrées absentes; conserve les rangs/localisations historiques.
for _mois, _jour, _date_csv, _nom, *_incipits in PROPER_OF_SAINTS:
    _rang = 2 if any(k in _nom.lower() for k in ('apostle', 'apostles', 'chair of st peter')) else 3
    # En 1962, saint Joseph ouvrier est le 1er mai et les apôtres Philippe
    # et Jacques le 11 mai (dates explicitement consignées dans le CSV).
    if (_mois, _jour) == (5, 1):
        SANCTORAL[(_mois, _jour)] = ("Saint Joseph ouvrier", 1, ["dim_I"])
    elif (_mois, _jour) == (5, 11):
        SANCTORAL[(_mois, _jour)] = ("Saints Philippe et Jacques, apôtres", 2, [])
    else:
        SANCTORAL.setdefault((_mois, _jour), (_nom, _rang, []))
del _mois, _jour, _date_csv, _nom, _incipits

# Référence explicite fournie pour le calendrier général romain de 1962.
from reference_1962 import REF_1962

RANG_CODE = {"I": 1, "II": 2, "III": 3, "Comm": 4, "Feria": 4}
RANGS_1962 = {cle: rang for cle, (rang, _libelle) in REF_1962.items()}

# Noms éditoriaux de la source en cas d'entrée manquante; les noms déjà
# présents dans SANCTORAL sont conservés pour préserver les correspondances CSV.
for _cle, (_rang_ref, _libelle_ref) in REF_1962.items():
    _ancien = SANCTORAL.get(_cle)
    _compat_noms = {(1,14): "Saint Hilaire",
                    (3,25): "Annonciation de la B.V.M.", (5,1): "Saint Joseph ouvrier",
                    (12,8): "Immaculée Conception de la B.V.M."}
    _nom_ref = _compat_noms.get(_cle, _libelle_ref)
    if _rang_ref == "Comm":
        SANCTORAL[_cle] = (_nom_ref, 4, ["commemoratio"])
    else:
        _flags = list(_ancien[2]) if _ancien else []
        if (_cle == (1, 13)) and "commemoratio" not in _flags:
            _flags.append("commemoratio")
        SANCTORAL[_cle] = (_nom_ref, RANG_CODE[_rang_ref], _flags)
# Les fêtes non listées par la source ne sont pas des fêtes du calendrier général.
for _cle in list(SANCTORAL):
    if _cle not in REF_1962:
        del SANCTORAL[_cle]
del _cle, _rang_ref, _libelle_ref, _ancien

# Célébrations mobiles ou sans entrée quotidienne dans la source synthétique.
SANCTORAL.update({
    (6, 23): ("Vigile de la Nativité de saint Jean-Baptiste", 2, []),
    (6, 28): ("Vigile des saints Pierre et Paul", 2, []),
    (8, 9): ("Vigile de saint Laurent", 3, []),
    (8, 14): ("Vigile de l'Assomption", 2, []),
    (4, 25): ("Saint Marc, évangéliste et Litanies majeures", 2, []),
})
RANGS_1962.update({(6,23): "II", (6,28): "II", (8,9): "III", (8,14): "II", (4,25): "II"})

# Particularités nationales / diocésaines demandées.
FRANCE_PARIS = {
    (1, 3): {"fr": ("Sainte Geneviève", 3), "paris": ("Sainte Geneviève", 1)},
    (2, 18): {"fr": ("Sainte Marie-Bernard Soubirous", 3)},
    (5, 30): {"fr": ("Sainte Jeanne d'Arc", 2)},
    (6, 3): {"fr": ("Sainte Clotilde", 3)},
    (10, 1): {"fr": ("Saint Rémi", 3)},
    (10, 3): {"fr": ("Sainte Thérèse de l'Enfant-Jésus", 2)},
    (10, 9): {"fr": ("Saint Denis et ses compagnons", 3)},
}

def classe_vers_rang(classe, flags=None):
    """Convertit la classe interne en code de rang de référence."""
    return {1: "I", 2: "II", 3: "III", 4: "Comm"}.get(classe, "Feria")

def noms_correspondent(reference, nom):
    """Comparaison souple des libellés abrégés de la référence française."""
    import unicodedata, re
    def tokens(x):
        x = unicodedata.normalize("NFD", x.lower())
        x = "".join(c for c in x if unicodedata.category(c) != "Mn")
        return {w for w in re.findall(r"[a-z]+", x) if len(w) > 3}
    a, b = tokens(reference), tokens(nom)
    stop = {"saint", "sainte", "saints", "vierge", "dame", "notre", "martyre", "martyr"}
    a -= stop; b -= stop
    return not a or not b or bool(a & b)

# ----------------------------------------------------------------------
# CALCULS DE BASE

def paques(annee):
    """Date de Pâques grégorienne, algorithme de Meeus/Jones/Butcher.

    Équivalent Python entier du calcul grégorien documenté dans
    moment.easter.js; accepte les années du calendrier datetime.
    """
    if not isinstance(annee, int):
        raise TypeError("annee doit être un entier")
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
    jour = (h + l - 7 * m + 114) % 31 + 1
    return date(annee, mois, jour)

def dim_sur_ou_avant(d):
    """Dimanche de la date ou le dimanche qui la précède."""
    return d - timedelta(days=d.isoweekday() % 7)

def dim_apres(d):
    """Premier dimanche strictement après la date."""
    return d + timedelta(days=7 - d.isoweekday() % 7)

def avent1(annee):
    """Premier dimanche de l'Avent (dimanche le plus proche du 30 novembre)."""
    s = date(annee, 11, 30)
    wd = s.isoweekday() % 7
    return s - timedelta(days=wd) if wd <= 3 else s + timedelta(days=7 - wd)

def dates_cles(a):
    p = paques(a)
    return {
        "paques": p, "septuagesime": p - timedelta(days=63),
        "cendres": p - timedelta(days=46), "rameaux": p - timedelta(days=7),
        "ascension": p + timedelta(days=39), "pentecote": p + timedelta(days=49),
        "trinite": p + timedelta(days=56), "corpus": p + timedelta(days=60),
        "sacre_coeur": p + timedelta(days=68), "avent1": avent1(a),
        "christ_roi": dim_sur_ou_avant(date(a, 10, 31)),
    }

# ----------------------------------------------------------------------
# TEMPOREL : (nom, classe, catégorie)

def temporal(d):
    a = d.year
    k = dates_cles(a)
    p = k["paques"]
    wd = d.isoweekday()
    nj = JOURS[wd - 1]
    dim = wd == 7

    # Avent : semaines comptées à partir du dimanche de chaque semaine.
    if k["avent1"] <= d <= date(a, 12, 24):
        n = (d - k["avent1"]).days // 7 + 1
        if dim:
            return (f"{n}e dimanche de l'Avent", 1, "avent")
        if d.month == 12 and d.day >= 17:
            return (f"{nj} avant Noël ({d.day} déc.)", 2, "avent")
        return (f"{nj} de la {n}e semaine de l'Avent", 3, "avent")

    # Temps de Noël et octave. Le dimanche entre le 2 et le 5 janvier
    # est la fête du Saint Nom; la Sainte Famille est le dimanche après l'Épiphanie.
    if d == date(a, 12, 25):
        return ("Nativité de N.S.J.C.", 1, "noel")
    if date(a, 12, 26) <= d <= date(a, 12, 31):
        if dim:
            return ("Dimanche dans l'octave de Noël", 2, "noel")
        return (f"{nj} dans l'octave de Noël", 2, "noel")
    if d == date(a, 1, 1):
        return ("Octave de Noël / Circoncision", 2, "noel")
    if date(a, 1, 2) <= d <= date(a, 1, 5):
        if dim:
            return ("Très Saint Nom de Jésus", 2, "noel")
        return (f"{nj} avant l'Épiphanie", 4, "noel")
    if d == date(a, 1, 6):
        return ("Épiphanie du Seigneur", 1, "epiphanie")

    # Après l'Épiphanie. Dimanche après le 6 janvier: Sainte Famille;
    # les dimanches suivants reprennent leur numérotation après l'Épiphanie.
    if date(a, 1, 6) < d < k["septuagesime"]:
        if dim:
            if d == dim_apres(date(a, 1, 6)):
                return ("Sainte Famille", 2, "epiphanie")
            n = (d - date(a, 1, 6)).days // 7 + 1
            return (f"{n}e dimanche après l'Épiphanie", 2, "epiphanie")
        return (f"{nj} après l'Épiphanie", 4, "epiphanie")

    # Temps de la Septuagésime.
    if k["septuagesime"] <= d < k["cendres"]:
        if dim:
            noms = ["Septuagésime", "Sexagésime", "Quinquagésime"]
            n = (d - k["septuagesime"]).days // 7
            return (noms[min(n, 2)], 2, "septuagesime")
        return (f"{nj} après la Septuagésime", 4, "septuagesime")

    # Carême : mercredi des Cendres à samedi avant les Rameaux.
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

    # Semaine Sainte.
    if k["rameaux"] <= d < p:
        noms = ["Dimanche des Rameaux", "Lundi saint", "Mardi saint", "Mercredi saint",
                "Jeudi saint", "Vendredi saint", "Samedi saint"]
        return (noms[(d - k["rameaux"]).days], 1, "semaine_sainte")

    # Pâques et octave (dimanche in albis inclus), Ascension, Pentecôte.
    if p <= d <= k["pentecote"]:
        i = (d - p).days
        if i == 0: return ("Dimanche de Pâques", 1, "pascal")
        if i < 7: return (f"{nj} dans l'octave de Pâques", 1, "pascal")
        if d == k["ascension"]: return ("Ascension de N.S.J.C.", 1, "pascal")
        if d == k["pentecote"]: return ("Dimanche de Pentecôte", 1, "pascal")
        if dim:
            n = i // 7
            if n == 1: return ("Dimanche in albis (2e de Pâques)", 1, "pascal")
            return (f"{n}e dimanche après Pâques", 2, "pascal")
        return (f"{nj} du temps pascal", 4, "pascal")

    # Temps après la Pentecôte.
    if k["pentecote"] < d < k["avent1"]:
        if d == k["trinite"]: return ("Sainte Trinité", 1, "pentecote")
        if d == k["corpus"]: return ("Corpus Christi", 1, "pentecote")
        if d == k["sacre_coeur"]: return ("Sacré-Cœur de Jésus", 1, "pentecote")
        if d == k["christ_roi"]: return ("Christ-Roi", 1, "pentecote")
        if d <= k["pentecote"] + timedelta(days=6):
            return (f"{nj} dans l'octave de Pentecôte", 1, "pentecote")
        # La numérotation suit les dimanches réellement célébrés. Le dimanche
        # du Christ-Roi est une fête propre et ne consomme pas un numéro; les
        # semaines restantes après lui reprennent donc sans saut.
        n = (d - k["pentecote"]).days // 7
        if dim_sur_ou_avant(d) > k["christ_roi"]:
            n -= 1
        if dim: return (f"{n}e dimanche après la Pentecôte", 2, "pentecote")
        return (f"{nj} de la {n}e semaine après la Pentecôte", 4, "pentecote")
    return ("Férie", 4, "ordinaire")

# ----------------------------------------------------------------------
# SANCTORAL ET OCCURRENCE / TRANSLATION

def propre_sanctoral(d):
    """Renvoie les propres du CSV pour la fête fixe du jour (ou None).

    Champs : name, introit, gradual, tract, alleluia, alleluia_pt,
    offertory, communion. La date alternative du 29 février suit le
    déplacement de saint Matthias et saint Gabriel.
    """
    s = sanctoral(d)
    if s is None:
        return None
    # Les entrées du CSV portant une date alternative sont normalisées ici.
    for mois, jour, date_csv, nom, introit, gradual, tract, alleluia, alleluia_pt, offertory, communion in PROPER_OF_SAINTS:
        leap_alias = (d.month, d.day) == (2, 28) and nom == "St Gabriel of Our Lady of Sorrows"
        date_match = (mois, jour) == (d.month, d.day) or leap_alias or ((d.month, d.day) == (2, 25) and nom == "St Matthias")
        if date_match:
            return {"name": nom, "introit": introit, "gradual": gradual, "tract": tract,
                    "alleluia": alleluia, "alleluia_pt": alleluia_pt,
                    "offertory": offertory, "communion": communion}
    return None

def sanctoral(d):
    """Fête du jour; les féries et les commémoraisons ne créent pas de fête propre."""
    bissextile = (d.year % 4 == 0 and (d.year % 100 != 0 or d.year % 400 == 0))
    if d.month == 2:
        if bissextile and d.day == 25: return ("Saint Matthias, apôtre", 2, [])
        if bissextile and d.day == 28: return ("Saint Gabriel de l'Addolorata", 3, [])
        if bissextile and d.day in (24, 27): return None
        if not bissextile and d.day == 24: return ("Saint Matthias, apôtre", 2, [])
        if not bissextile and d.day == 27: return ("Saint Gabriel de l'Addolorata", 3, [])
    # Le dimanche du Très Saint Nom (2–5 janvier), à défaut le 2 janvier.
    nom_jesus = next((date(d.year, 1, j) for j in range(2, 6)
                      if date(d.year, 1, j).weekday() == 6), date(d.year, 1, 2))
    if d == nom_jesus: return ("Saint Nom de Jésus", 2, ["seigneur"])
    epiphanie = date(d.year, 1, 6)
    famille = epiphanie + timedelta(days=(6-epiphanie.weekday()) % 7 or 7)
    if d == famille: return ("Sainte Famille", 2, ["seigneur"])
    k = dates_cles(d.year)
    if d == k["christ_roi"]: return ("Christ-Roi", 1, ["seigneur", "dim_I"])
    if d == (date(d.year, 11, 3) if date(d.year, 11, 2).isoweekday() == 7 else date(d.year, 11, 2)):
        return ("Commémoration de tous les fidèles défunts", 1, ["seigneur"])
    passion = k["paques"] - timedelta(days=14)
    douleur = passion + timedelta(days=(4-passion.weekday()) % 7 or 7)
    if d == douleur: return ("Commémoration des Sept Douleurs de la B.V.M.", 4, ["commemoratio"])
    s = SANCTORAL.get((d.month, d.day))
    return s

def celebration_naturelle(d):
    """Célébration du jour avant la translation des fêtes empêchées."""
    t_nom, t_cl, t_cat = temporal(d)
    s = sanctoral(d)
    if s is None:
        return (t_nom, t_cl, "", False)
    s_nom, s_cl, s_flags = s
    if "commemoratio" in s_flags:
        return (t_nom, t_cl, f"commémoraison : {s_nom}", False)
    dim = d.isoweekday() == 7
    # Les dimanches I classe et les jours de la Semaine Sainte/octave de Pâques
    # prévalent; les solennités empêchées sont ensuite examinées pour translation.
    if t_cl == 1:
        return (t_nom, t_cl, "", bool(s_cl == 1 and s_nom != t_nom))
    if dim:
        if s_cl == 1:
            return (s_nom, s_cl, "", False)
        if s_cl == 2 and "seigneur" in s_flags:
            return (s_nom, s_cl, "", False)
        return (t_nom, t_cl, "", False)
    if t_cl < s_cl:
        return (t_nom, t_cl, "", False)
    if t_cl > s_cl:
        return (s_nom, s_cl, "", False)
    return (s_nom, s_cl, f"(temporal : {t_nom})", False)

def fete_empechee(d):
    """Retourne une fête sanctorale de classe I empêchée par le temporal."""
    s = sanctoral(d)
    if not s or s[1] != 1:
        return None
    nom, cl, flags = s
    t_nom, t_cl, t_cat = temporal(d)
    if t_cl == 1 and t_nom != nom:
        # « dim_I » dans la table signifie une fête de classe I qui n'est pas
        # autorisée à être transférée selon l'ancienne convention du fichier.
        if "dim_I" in flags:
            return None
        return s
    return None

def premier_jour_libre(d):
    """Premier jour postérieur sans temporal de I classe ni fête de I/II classe."""
    x = d + timedelta(days=1)
    for _ in range(45):
        t_nom, t_cl, _ = temporal(x)
        s = sanctoral(x)
        if t_cl > 1 and not (s and s[1] <= 2):
            return x
        x += timedelta(days=1)
    return None

def transferts_vers(d):
    """Recherche les fêtes I classe empêchées reportées à cette date."""
    for delta in range(1, 40):
        origine = d - timedelta(days=delta)
        f = fete_empechee(origine)
        if f and premier_jour_libre(origine) == d:
            return (f[0], origine)
    return None

def celebration(d, region=None):
    """Retourne (nom, classe, note); region: None (romain), 'fr' ou 'paris'."""
    if region not in (None, "fr", "paris"):
        raise ValueError("region doit être None, 'fr' ou 'paris'")
    if region:
        regionale = FRANCE_PARIS.get((d.month, d.day), {}).get(region)
        if regionale:
            t_nom, t_cl, _ = temporal(d)
            g = sanctoral(d)
            # Une régionale supérieure prévaut sur une fête ordinaire; le temporal
            # de classe I et les jours majeurs demeurent prioritaires.
            if (t_cl != 1 or (d.month, d.day) == (5, 30)) and not (g and g[1] == 1):
                return (regionale[0], regionale[1], "")
    tr = transferts_vers(d)
    if tr:
        return (tr[0], 1, f"transférée du {tr[1].strftime('%d/%m')}")
    nom, cl, note, _ = celebration_naturelle(d)
    return (nom, cl, note)

# ----------------------------------------------------------------------
# AFFICHAGE ET FICHIERS DE PROPRES (interface originale conservée)

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
    """Nom de fichier Tempora/ selon la convention Divinum Officium."""
    a = d.year
    k = dates_cles(a)
    p = k["paques"]
    wd = d.isoweekday() % 7
    if k["avent1"] <= d <= date(a, 12, 24):
        n = (d - k["avent1"]).days // 7 + 1
        return f"Tempora/Adv{n}-{wd}"
    if d.month == 12 and d.day >= 26:
        return f"Tempora/Nat{d.day:02d}"
    if d.month == 1 and 2 <= d.day <= 5:
        return f"Tempora/Nat{d.day:02d}"
    if (d.month, d.day) in [(12, 25), (1, 1), (1, 6)]:
        return fichier_sancti(d)
    if d < k["septuagesime"]:
        n = (d - date(a, 1, 6)).days // 7 + 1
        return f"Tempora/Epi{n}-{wd}"
    if d < k["cendres"]:
        n = (d - k["septuagesime"]).days // 7 + 1
        return f"Tempora/Quadp{n}-{wd}"
    if d < k["cendres"] + timedelta(days=4):
        return f"Tempora/Quadp3-{wd}"
    if d < k["rameaux"]:
        n = (d - (k["cendres"] + timedelta(days=4))).days // 7 + 1
        return f"Tempora/Quad{n}-{wd}"
    if d < p:
        return f"Tempora/Quad6-{wd}"
    if d <= k["pentecote"]:
        n = (d - p).days // 7
        return f"Tempora/Pasc{n}-{wd}"
    n = (d - k["pentecote"]).days // 7
    if n == 0:
        return f"Tempora/Pasc7-{wd}"
    n = (d - k["pentecote"]).days // 7
    if n == 0:
        return f"Tempora/Pasc7-{wd}"
    # Le dimanche du Christ-Roi n'est pas numéroté dans cette série; les
    # dimanches suivants reprennent la suite, et les propres suivent ce numéro.
    if dim_sur_ou_avant(d) > k["christ_roi"]:
        n -= 1
    return f"Tempora/Pent{n:02d}-{wd}"

def fichiers_du_jour(d):
    """Liste ordonnée des propres selon la célébration retenue."""
    nom, cl, note = celebration(d)
    tr = transferts_vers(d)
    s = sanctoral(d)
    fichiers = []
    if tr:
        fichiers.append(fichier_sancti(tr[1]))
    elif s and s[0] == nom:
        fichiers.append(fichier_sancti(d))
    fichiers.append(fichier_temporal(d))
    return fichiers

def verifier(annee):
    """Liste triée des fichiers manquants pour une année donnée."""
    manquants = set()
    d = date(annee, 1, 1)
    while d.year == annee:
        for f in fichiers_du_jour(d):
            if not (Path("data/Latin") / f"{f}.txt").exists():
                manquants.add(f)
        d += timedelta(days=1)
    return sorted(manquants)

if __name__ == "__main__":
    if len(sys.argv) == 1:
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

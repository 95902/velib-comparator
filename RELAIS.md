# Fichier relais : implémentation des issues

Ce fichier sert de **relais** entre les membres de l'équipe (et les sessions de travail) :
il dit dans quel ordre les issues GitHub sont implémentées, sur quelle branche,
par quelle Pull Request, et ce qui a été décidé en chemin. Avant de reprendre le travail,
lis ce fichier ; après chaque PR fusionnée, mets à jour sa ligne.

## Règles suivies (issue #3)

- Une branche par issue, partie de `main` à jour (`git pull origin main`).
- La PR contient `Closes #N` : l'issue se ferme automatiquement à la fusion.
- Avant de fusionner : `python -m pytest` passe, et le script concerné a été lancé pour de vrai.
- `.env` n'est jamais envoyé ; `data/brut/velib.csv` est remis à sa version de `main` avant chaque commit
  (il est réécrit à chaque téléchargement).

## Décisions prises (contrat #4)

| Sujet | Décision |
|---|---|
| Stations hors service | Gardées dans le tableau nettoyé avec une colonne `en_service` (booléen), **exclues des indicateurs**, en gris sur la carte. |
| Capacité nulle | Les 3 stations concernées sont hors service : `en_service` est forcé à faux, jamais de division par 0. |
| `taux_remplissage` | `vélos / (vélos + bornes libres)`, en %, arrondi à 0,1 : reste entre 0 et 100 %. |
| `zone` | Commune normalisée ; pour Paris, `"paris N"` d'après les premiers chiffres du `stationcode` (`10202` → `paris 10`, `3012` → `paris 3`). Les 2 codes hors règle (`60001`, `60002`) restent en `"paris"`. |
| `normaliser()` | Minuscules, sans accents, tirets et apostrophes remplacés par des espaces (`Saint-Denis` → `saint denis`). |
| Météo | API Météo-France **DPObs v2** (la clé est abonnée à la v2, pas à la v1), `station/infrahoraire-6m`, station Paris-Montsouris `75114001`. Champs : `t` (K), `ff` (m/s), `rr_per` (mm sur 6 min), `validity_time`. |
| Météo et usage (#22) | L'API ne donne pas les trajets : moins de cyclistes → taux de remplissage plus haut ; électriques préférés → part d'électriques en station plus basse. Pluie comparée **à créneau égal** (heure de Paris, semaine / week-end) pour ne pas confondre avec l'heure de pointe. |
| Trajet (#26) | `distance_m()` (haversine) et `station_conseillee()` dans `src/trajet.py` ; `charger_utilisateurs()` dans `src/recuperation.py`. Distance arrondie au mètre, puis départage par le nombre de vélos / bornes. |
| Gagnant | Plus grand = mieux, sauf `stations_vides` et `pct_stations_vides` (moins = mieux). Valeurs égales → `Égalité`. |

## Avancement

| Issue | Rôle | Sujet | Branche | PR | Statut |
|---|---|---|---|---|---|
| — | Équipe | Fichier relais | `relais` | #27 | ✅ Fusionnée |
| #8 | A | `nettoyer_velib()`, `normaliser()`, rapport | `nettoyage-velib` | #28 | ✅ Fusionnée |
| #6 | B | `stats_commune()` + `tests/donnees_test.csv` | `stats-commune` | #29 | ✅ Fusionnée |
| #9 | B | `comparer()` et ses tests | `comparer` | #30 | ✅ Fusionnée |
| #10 | C | `meteo_actuelle()` | `meteo` | #31 | ✅ Fusionnée |
| #11 | A | Tests du nettoyage, vraies données | `tests-nettoyage` | #32 | ✅ Fusionnée |
| #12 | B | `compare.py` (argparse + rich) | `compare-cli` | #33 | ✅ Fusionnée |
| #13 | C | Onglet Duel de `app.py` | `app-duel` | #34 | ✅ Fusionnée |
| #14 | A | Colonne `zone` (arrondissements) | `zone-arrondissements` | #35 | ✅ Fusionnée |
| #15 | B | Indicateurs relatifs, zones dans `compare.py` | `indicateurs-relatifs` | #36 | ✅ Fusionnée |
| #17 | A | Gestion des erreurs | `gestion-erreurs` | #37 | ✅ Fusionnée |
| #16 | C | Onglets Météo, Carte, rapport, bouton Actualiser | `app-meteo-carte` | #38 | ✅ Fusionnée |
| #25 | C | Cache et heure des données | `cache-temps-reel` | #39 | ✅ Fusionnée |
| #26 | A/B/C | Utilisateurs et station conseillée | `mon-trajet` | #40 | ✅ Fusionnée |
| #21 | Bonus | Collecte de l'historique | `collecte-historique` | #41 | ✅ Fusionnée |
| #22 | Bonus | Effet de la pluie (outil prêt ; issue laissée ouverte : conclusion après quelques jours de collecte) | `effet-pluie` | #42 | ✅ Fusionnée |
| #18 | B | Relecture et nettoyage | `relecture` | #43 | ✅ Fusionnée |
| #19 | C | README | `readme` | #44 | ✅ Fusionnée |
| — | C | Mon trajet : stations autour du trajet, vélos mécaniques / électriques, lieux réalistes | `trajet-stations-proches` | #45 | ✅ Fusionnée |
| — | C | Mon trajet : filtre vélo électrique / mécanique | `filtre-type-velo` | #46 | ✅ Fusionnée |
| — | C | Carte : filtre vélo électrique / mécanique | `carte-type-velo` | #47 | ✅ Fusionnée |
| — | A | Panne de l'open data : réponses vides refusées, CSV de secours protégé | `donnees-velib-invalides` | #48 | ✅ Fusionnée |
| #22 | Bonus | Météo et vélos : part d'électriques, température, comparaison à heure égale | `analyse-meteo-usage` | #49 | ✅ Fusionnée |
| #20 | Équipe | Checklist finale | — | — | Vérifiée en commentaire sur l'issue (points humains à cocher en équipe) |

## Points à faire par l'équipe (non automatisables)

- Chaque membre relit le code des autres rôles et sait l'expliquer (#18, #20).
- Questions ouvertes de #26 : version simple codée (utilisateurs fixés dans `data/utilisateurs.json`, pas de préférence électrique, pas de station de secours). À rediscuter en équipe si on veut aller plus loin.
- Répéter la présentation (#20).

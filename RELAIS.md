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
| Gagnant | Plus grand = mieux, sauf `stations_vides` et `pct_stations_vides` (moins = mieux). Valeurs égales → `Égalité`. |

## Avancement

| Issue | Rôle | Sujet | Branche | PR | Statut |
|---|---|---|---|---|---|
| — | Équipe | Fichier relais | `relais` | #27 | ✅ Fusionnée |
| #8 | A | `nettoyer_velib()`, `normaliser()`, rapport | `nettoyage-velib` | #28 | ✅ Fusionnée |
| #6 | B | `stats_commune()` + `tests/donnees_test.csv` | `stats-commune` | #29 | ✅ Fusionnée |
| #9 | B | `comparer()` et ses tests | `comparer` | — | ⏳ À faire |
| #10 | C | `meteo_actuelle()` | `meteo` | — | ⏳ À faire |
| #11 | A | Tests du nettoyage, vraies données | `tests-nettoyage` | — | ⏳ À faire |
| #12 | B | `compare.py` (argparse + rich) | `compare-cli` | — | ⏳ À faire |
| #13 | C | Onglet Duel de `app.py` | `app-duel` | — | ⏳ À faire |
| #14 | A | Colonne `zone` (arrondissements) | `zone-arrondissements` | — | ⏳ À faire |
| #15 | B | Indicateurs relatifs, zones dans `compare.py` | `indicateurs-relatifs` | — | ⏳ À faire |
| #17 | A | Gestion des erreurs | `gestion-erreurs` | — | ⏳ À faire |
| #16 | C | Onglets Météo, Carte, rapport, bouton Actualiser | `app-meteo-carte` | — | ⏳ À faire |
| #25 | C | Cache et heure des données | `cache-temps-reel` | — | ⏳ À faire |
| #26 | A/B/C | Utilisateurs et station conseillée | `mon-trajet` | — | ⏳ À faire |
| #21 | Bonus | Collecte de l'historique | `collecte-historique` | — | ⏳ À faire |
| #22 | Bonus | Effet de la pluie | `effet-pluie` | — | ⏳ À faire |
| #18 | B | Relecture et nettoyage | `relecture` | — | ⏳ À faire |
| #19 | C | README | `readme` | — | ⏳ À faire |
| #20 | Équipe | Checklist finale | — | — | Vérifiée en commentaire sur l'issue (points humains à cocher en équipe) |

## Points à faire par l'équipe (non automatisables)

- Chaque membre relit le code des autres rôles et sait l'expliquer (#18, #20).
- Les questions ouvertes de #26 (utilisateurs ajoutés depuis l'appli, préférence électrique, station de secours) restent à trancher.
- Répéter la présentation (#20).

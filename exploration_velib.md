# Exploration des données Vélib

Constats sur le CSV brut, à utiliser pour écrire le nettoyage (issue #8).

- **Données** : `data/brut/velib.csv`, téléchargé le 6 novembre 2026 (relevé le plus récent : 10 h 48 UTC)
- **Script** : `python explorer_velib.py` (relance-le pour retrouver ces chiffres sur un nouveau téléchargement)
- **Source** : API open data Paris, jeu `velib-disponibilite-en-temps-reel`

Les chiffres changent à chaque téléchargement ; ce sont les règles qui comptent.

## Vue d'ensemble

- 1 520 stations, 16 colonnes
- 69 communes ; Paris en concentre 997, puis Boulogne-Billancourt (30), Montreuil (23), Issy-les-Moulineaux (22), Pantin (21)
- Les coordonnées sont toutes en Île-de-France (latitude 48,74 à 48,96 ; longitude 2,17 à 2,54) : aucune valeur aberrante

## Colonnes du brut

| Colonne brute | Type lu | Remarque | Devient (contrat) |
|---|---|---|---|
| `stationcode` | texte | Lu comme un nombre si on oublie `dtype={"stationcode": str}` | `stationcode` |
| `name` | texte | | `name` |
| `is_installed`, `is_renting`, `is_returning` | texte `OUI` / `NON` | Voir « Stations hors service » | `en_service` (proposition) |
| `capacity` | entier | De 0 à 410 | `capacity` |
| `numbikesavailable`, `numdocksavailable` | entier | | idem |
| `mechanical`, `ebike` | entier | Leur somme vaut toujours `numbikesavailable` | idem |
| `duedate` | texte (date) | Heure du dernier relevé de la station | non utilisée pour l'instant |
| `nom_arrondissement_communes` | texte | Paris n'est pas découpé en arrondissements | `commune`, puis `commune_norm` |
| `code_insee_commune` | entier | Utile pour `zone` en phase 4 | non utilisée pour l'instant |
| `station_opening_hours` | vide | Vide sur les 1 520 stations | à supprimer |
| `coordonnees_geo.lat`, `coordonnees_geo.lon` | décimal | Séparées par `json_normalize` | `lat`, `lon` |

## Constats

### Doublons
Aucun : 0 ligne identique et 0 `stationcode` en double. On garde quand même la règle dans le nettoyage, car un autre téléchargement peut en contenir.

### Stations hors service
- 24 stations ont `is_renting` et `is_returning` à `NON` (les deux vont toujours ensemble).
- Parmi elles, 3 ont aussi `is_installed` à `NON`.
- Exemples : `Raspail - Bac`, `Invalides - Quai d'Orsay` (la plus grande station, 410 bornes), `Mairie du 10ème`.

**Proposition** : ne pas les supprimer, mais les garder avec une colonne `en_service` (vrai / faux).
- La carte les affiche **en gris** : l'utilisateur voit qu'une station existe mais qu'elle est fermée.
- Les indicateurs (`stats_commune()`) ne comptent **que** les stations en service. Sinon une station fermée compterait comme « vide ».
- Le rapport de nettoyage indique combien de stations sont hors service.

À valider en équipe dans l'issue #4 (Contrat), car cela change la règle de la phase 2 et la checklist finale.

### Capacités nulles
3 stations ont une capacité de 0. Ce sont les 3 stations non installées : elles sont donc déjà hors service. Elles restent en gris sur la carte avec les autres, mais `stats_commune()` ne doit jamais diviser par leur capacité.

### Vélos + bornes libres comparés à la capacité
| Cas | Stations |
|---|---|
| Égal à `capacity` | 745 |
| Inférieur (bornes cassées ou bloquées) | 760 |
| Supérieur (vélos en surplus) | 15 |

Exemple de surplus : `BNF - Bibliothèque Nationale de France`, 64 vélos pour 42 bornes.

Conséquence pour `taux_remplissage` (décision à prendre dans l'issue #4) :
- `velos / capacity` peut dépasser 100 % ;
- `velos / (velos + bornes libres)` reste entre 0 et 100 % et ne compte que les bornes qui fonctionnent.

### Stations vides et pleines
- 152 stations n'ont aucun vélo.
- 35 stations n'ont aucune borne libre.

Ces chiffres incluent les stations hors service : il faudra les recalculer sur les seules stations en service.

### Très grandes stations
`Invalides - Quai d'Orsay` (410 bornes) et une autre de 409 bornes faussent les moyennes « par station ». C'est un point à garder en tête pour l'indicateur « vélos par station » (phase 4).

## Ce que le nettoyage doit faire (résumé pour #8)

- [ ] Lire le CSV avec `dtype={"stationcode": str}`
- [ ] Supprimer les doublons de `stationcode`
- [ ] Supprimer `station_opening_hours`
- [ ] Renommer `coordonnees_geo.lat` / `coordonnees_geo.lon` en `lat` / `lon`, et `nom_arrondissement_communes` en `commune`
- [ ] Créer `commune_norm` avec `normaliser()`
- [ ] Créer `en_service` (vrai si `is_installed`, `is_renting` et `is_returning` valent tous `OUI`) au lieu de supprimer les stations hors service, si l'équipe valide
- [ ] Indiquer dans le rapport : doublons retirés, stations hors service, capacités nulles

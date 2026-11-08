# Bibliothèques du projet Comparateur Vélib

Ce document liste toutes les bibliothèques utilisées dans le projet, avec leur rôle.

Il y en a deux sortes :
- celles **à installer** avec `pip` (listées dans `requirements.txt`) ;
- celles **déjà incluses dans Python** (rien à installer).

---

## 1. Bibliothèques à installer

| Bibliothèque | À quoi elle sert | Où on l'utilise |
|---|---|---|
| **requests** | Envoyer des requêtes sur Internet pour récupérer des données depuis une API (comme un navigateur, mais en code). | Télécharger les données Vélib et Météo-France |
| **pandas** | Manipuler des données sous forme de tableau (lignes et colonnes) : filtrer, trier, calculer des moyennes, supprimer les doublons. C'est l'outil principal du nettoyage. | Nettoyage, normalisation, calcul des indicateurs |
| **python-dotenv** | Lire un fichier `.env` qui contient des informations secrètes, comme la clé API, pour ne pas les écrire dans le code. | Clé de l'API Météo-France |
| **rich** | Afficher de jolis tableaux en couleur dans le terminal. | Affichage côte à côte de la commande `compare.py` |
| **streamlit** | Créer une application web (une page dans le navigateur) uniquement en Python, sans HTML ni JavaScript. Fournit boutons, listes déroulantes, colonnes, graphiques et carte. | L'interface `app.py` |
| **pytest** | Lancer des tests automatiques qui vérifient que les fonctions donnent le bon résultat. | Tester le nettoyage, les indicateurs, le gagnant, la météo, le trajet (`pytest`) |
| **pydeck** *(installée avec streamlit)* | Dessiner une carte avec des points colorés et une info-bulle au survol. | Onglets Carte et Mon trajet de `app.py` |
| **jupyter** *(optionnel)* | Écrire et exécuter du code bloc par bloc, en voyant le résultat tout de suite. Pratique pour explorer les données avant de coder. | Exploration des données |

### Installation

Avec l'environnement virtuel activé :

```bash
pip install -r requirements.txt
```

---

## 2. Modules déjà inclus dans Python

| Module | À quoi il sert | Où on l'utilise |
|---|---|---|
| **argparse** | Lire les mots tapés après la commande (`Paris` et `Montreuil` dans `python compare.py Paris Montreuil`). | La commande `compare.py` |
| **unicodedata** | Enlever les accents d'un texte (`Créteil` → `Creteil`). | Normalisation des noms de communes |
| **difflib** | Trouver les mots qui ressemblent à un autre, pour proposer « Vouliez-vous dire Montreuil ? » en cas de faute de frappe. | Message d'erreur si la commune est introuvable |
| **os** | Lire des variables de l'ordinateur, comme la clé API chargée depuis `.env`. | `src/meteo.py` |
| **pathlib** | Manipuler les chemins de fichiers et de dossiers (`data/brut/velib.csv`) de façon fiable sur Windows comme sur Mac. | Enregistrer et relire les fichiers de données |
| **json** | Lire un fichier `.json` (liste d'utilisateurs et de leurs lieux). | `charger_utilisateurs()` |
| **time** | Attendre entre deux relevés (`time.sleep`). | `collecter.py` |
| **math** | Fonctions mathématiques (racine carrée, sinus…), utiles pour calculer une distance entre deux points GPS. | `distance_m()` : distance entre un lieu et une station Vélib (haversine) |

---

## 3. Les API utilisées

| API | À quoi elle sert |
|---|---|
| **Vélib – disponibilité en temps réel** (Open Data Paris) | Donne pour chaque station : capacité, vélos disponibles, bornes libres, commune, coordonnées. |
| **Météo-France – Données Publiques d'Observation (v2)** | Donne les mesures des stations météo : température, humidité, vent, pluie. Nécessite une clé API gratuite. On lit la station Paris-Montsouris toutes les 6 minutes (`station/infrahoraire-6m`). |
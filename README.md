# Comparateur Vélib

Compare la disponibilité des Vélib entre deux communes (ou arrondissements de Paris), en ligne de commande ou dans une application web.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (sur macOS / Linux : source .venv/bin/activate)
pip install -r requirements.txt
```

## Clé API Météo-France

L'application affiche la météo du moment grâce à l'API Météo-France. Chacun crée **sa propre clé**, qui ne doit jamais être envoyée sur GitHub.

1. Créer un compte sur https://portail-api.meteofrance.fr et confirmer l'e-mail.
2. Dans le catalogue des API, choisir **Données Publiques d'Observation** et s'y abonner (gratuit).
3. Dans « Mes API », générer une clé de type **API Key** (choisir sa durée de validité) et la copier.
4. Créer le fichier `.env` à partir du modèle, puis y coller la clé :
   ```powershell
   Copy-Item .env.example .env
   ```
   ```
   METEO_FRANCE_API_KEY=ta_cle_ici
   ```
5. Vérifier que `git status` n'affiche pas `.env` : il est ignoré par `.gitignore`.

Quand la clé expire, il suffit d'en générer une nouvelle et de remplacer la valeur dans `.env`.

## Utilisation

```bash
python -m src.recuperation   # télécharge les données Vélib dans data/brut/velib.csv
python explorer_velib.py     # affiche les constats sur les données brutes
streamlit run app.py         # ouvre l'application web
```

La page d'accueil indique si la clé Météo-France a bien été trouvée.

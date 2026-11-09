# 🚲 Comparateur Vélib — Présentation

> Comparer en direct la disponibilité des Vélib entre deux communes (ou arrondissements de Paris),
> en ligne de commande ou dans une application web, avec la météo du moment.

**Équipe** : A (données) · B (calculs) · C (interface)
**Dépôt** : `95902/velib-comparator` · 49 PR fusionnées · 78 tests qui passent

> 💡 Les schémas sont écrits en **Mermaid** : du texte simple, modifiable dans Sublime Text.
> Ils s'affichent en graphiques sur GitHub, dans VS Code (extension *Markdown Preview Mermaid*),
> ou en collant un bloc sur https://mermaid.live pour l'exporter en PNG/SVG pour les diapos.

---

## 1. Le problème

Le matin, on veut savoir **où trouver un vélo** et **où le déposer**.
Paris publie l'état de ses ~1 500 stations Vélib en temps réel, mais sous forme de données brutes :
noms de communes incohérents, doublons, stations hors service, capacités à zéro…

**Notre objectif** :
1. récupérer ces données de façon fiable, même si l'API tombe ;
2. les nettoyer selon un **contrat** commun à toute l'équipe ;
3. calculer des indicateurs comparables entre deux zones ;
4. les présenter simplement : un terminal, une appli web, une carte, la météo.

---

## 2. Vue d'ensemble : sources, cœur, sorties

Trois **sources de données** entrent, un **cœur de calcul** commun les transforme,
trois **points d'entrée** les exploitent.

```mermaid
flowchart LR
    subgraph SOURCES["🌐 Sources de données"]
        API_V[("API open data<br/>Paris – Vélib<br/>temps réel")]
        API_M[("API Météo-France<br/>DPObs v2<br/>Paris-Montsouris")]
        JSON[("data/utilisateurs.json<br/>lieux habituels")]
    end

    subgraph LOCAL["💾 Fichiers locaux"]
        CSV[("data/brut/velib.csv<br/>dernier bon téléchargement")]
        HIST[("data/historique/releves.csv<br/>un relevé / 15 min")]
        ENV[(".env<br/>clé API — jamais sur GitHub")]
    end

    subgraph COEUR["⚙️ Cœur : src/"]
        REC[recuperation.py]
        NET[nettoyage.py]
        IND[indicateurs.py]
        COMP[comparaison.py]
        MET[meteo.py]
        TRA[trajet.py]
        COL[collecte.py]
        PLU[analyse_pluie.py]
    end

    subgraph SORTIES["🖥️ Points d'entrée"]
        CLI["compare.py<br/>terminal (rich)"]
        APP["app.py<br/>appli web (Streamlit)"]
        BOT["collecter.py<br/>collecte en continu"]
    end

    API_V --> REC
    REC <--> CSV
    JSON --> REC
    API_M --> MET
    ENV --> MET
    COL <--> HIST

    REC --> NET --> IND --> COMP
    IND --> COL
    MET --> COL
    COL --> PLU
    NET --> TRA

    COEUR --> CLI
    COEUR --> APP
    COEUR --> BOT
```

---

## 3. Dépendances entre modules (qui importe qui)

Chaque flèche = un `import`. Le graphe **n'a pas de boucle** : on peut tester chaque module seul.
`nettoyage.py` est la fondation ; les trois scripts à la racine ne font qu'assembler les briques.

```mermaid
flowchart TD
    classDef entree fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef coeur fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef feuille fill:#fef9c3,stroke:#ca8a04,color:#713f12

    APP["app.py"]:::entree
    CLI["compare.py"]:::entree
    BOT["collecter.py"]:::entree
    EXP["explorer_velib.py"]:::entree

    REC["recuperation.py<br/>telecharger_velib()<br/>charger_velib_brut()<br/>charger_utilisateurs()"]:::feuille
    NET["nettoyage.py<br/>nettoyer_velib()<br/>normaliser()<br/>zones_disponibles()"]:::feuille
    MET["meteo.py<br/>meteo_actuelle()"]:::feuille
    TRA["trajet.py<br/>distance_m()<br/>station_conseillee()"]:::feuille
    COMP["comparaison.py<br/>comparer()<br/>bilan()"]:::feuille
    PLU["analyse_pluie.py<br/>effet_pluie()<br/>conclusion()"]:::feuille

    IND["indicateurs.py<br/>stats_commune()"]:::coeur
    COL["collecte.py<br/>releve_zones()<br/>lire_historique()"]:::coeur

    IND --> NET
    COL --> IND

    APP --> REC & NET & IND & COMP & MET & TRA & COL & PLU
    CLI --> REC & NET & IND & COMP
    BOT --> REC & NET & MET & COL
    EXP --> REC
```

🟦 points d'entrée · 🟩 modules qui en utilisent d'autres · 🟨 modules indépendants

---

## 4. Le parcours d'une donnée : de l'API à l'écran

Le même chemin sert au terminal et à l'appli web. Entre chaque étape, la forme de la donnée
est fixée par le **contrat** (issue #4).

```mermaid
flowchart LR
    A[("API Vélib<br/>JSON")] -->|"telecharger_velib()<br/>json_normalize"| B["Tableau brut<br/>~1 500 stations"]
    B -->|"nettoyer_velib()"| C["Tableau nettoyé<br/>14 colonnes du contrat"]
    B -.->|"en parallèle"| R["Rapport de nettoyage<br/>doublons, hors service,<br/>capacité nulle…"]
    C -->|"stats_commune(df, 'Paris 11')"| D1["dict stats A"]
    C -->|"stats_commune(df, 'Montreuil')"| D2["dict stats B"]
    D1 & D2 -->|"comparer()"| E["7 lignes :<br/>indicateur, A, B, gagnant"]
    E -->|"bilan()"| F["🏆 Gagnant global<br/>ou Égalité"]
    E --> G1["Tableau rich<br/>compare.py"]
    E --> G2["Onglet Duel<br/>app.py"]
```

**Les étapes du nettoyage** (`nettoyer_velib`) :

```mermaid
flowchart TD
    S([Tableau brut]) --> N0["0 · Retire les stations incomplètes<br/>sans code, nom, commune ou position"]
    N0 --> N1["1 · Retire les doublons<br/>une ligne par stationcode"]
    N1 --> N2["2 · Renomme selon le contrat<br/>lat, lon, commune"]
    N2 --> N3["3 · Convertit en entiers<br/>capacity, vélos, bornes…"]
    N3 --> N4{"4 · En service ?<br/>installée + prête + rend<br/>+ capacité > 0"}
    N4 -->|oui| OK["en_service = True"]
    N4 -->|non| KO["en_service = False<br/>gardée, grisée sur la carte,<br/>exclue des indicateurs"]
    OK & KO --> N5["Ajoute commune_norm et zone<br/>'paris 11' d'après le stationcode"]
    N5 --> F([Tableau nettoyé + rapport])
```

---

## 5. Les indicateurs comparés

| Indicateur | Calcul | Gagnant |
|---|---|---|
| Stations en service | nombre de stations `en_service` | plus grand |
| Vélos disponibles | somme des vélos | plus grand |
| Taux de remplissage | vélos / (vélos + bornes libres) | plus grand |
| Stations vides | stations sans vélo | **plus petit** |
| Stations vides (%) | vides / stations en service | **plus petit** |
| Vélos par station | vélos / stations | plus grand |
| Part d'électriques | électriques / vélos | plus grand |

**Décision d'équipe** : on divise par `vélos + bornes libres` plutôt que par `capacity`, car
15 stations ont plus de vélos que de bornes (BNF : 64 vélos pour 42 bornes). Sinon on dépasserait 100 %.

---

## 6. Robustesse : que se passe-t-il si l'API tombe ?

On garde toujours le **dernier bon téléchargement** comme secours, et une réponse vide
ne l'écrase jamais (PR #48).

```mermaid
flowchart TD
    START(["charger_velib_brut()"]) --> DL["Appel API Vélib"]
    DL --> Q1{"Réponse OK ?"}
    Q1 -->|oui| V{"verifier_velib()<br/>colonnes présentes,<br/>< 50 % de stations incomplètes ?"}
    V -->|oui| SAVE["Écrit data/brut/velib.csv"] --> LIVE(["✅ Données en direct"])
    V -->|non : open data en panne| FALL
    Q1 -->|"non : pas d'internet,<br/>erreur HTTP"| FALL{"velib.csv existe<br/>et est valide ?"}
    FALL -->|oui| OLD(["⚠️ Dernières données connues<br/>+ bandeau d'avertissement"])
    FALL -->|non| ERR(["❌ DonneesIndisponibles<br/>message clair, pas de plantage"])
```

Autres erreurs gérées : commune mal tapée (`montreuill` → « Vouliez-vous dire Montreuil ? »),
clé Météo-France absente (tout marche sauf l'onglet Météo).

---

## 7. L'application web : onglets et cache

Streamlit garde les données en mémoire pour ne pas rappeler les API à chaque clic.
Le bouton **🔄 Actualiser** vide ce cache.

```mermaid
flowchart LR
    subgraph CACHE["🧠 Cache Streamlit"]
        CV["charger_velib()<br/>garde 1 min"]
        CM["charger_meteo()<br/>garde 10 min"]
    end

    API_V[("API Vélib")] --> CV
    API_M[("Météo-France")] --> CM
    HIST[("releves.csv")] --> P
    JSON[("utilisateurs.json")] --> T

    CV --> D["⚔️ Duel<br/>stats_commune + comparer"]
    CV --> T["🧭 Mon trajet<br/>station_conseillee"]
    CV --> C["🗺️ Carte<br/>pydeck, filtre ⚡/🚲"]
    CM --> M["🌦️ Météo<br/>température, vent, pluie"]
    P["🌧️ Météo et vélos<br/>analyse_pluie"]
    CV --> N["🧹 Nettoyage<br/>rapport"]

    BTN(["🔄 Actualiser"]) -. vide .-> CACHE
```

---

## 8. Bonus : « Mon trajet »

Pour un utilisateur et un trajet (ex. domicile → travail), on conseille **où prendre**
et **où déposer** un vélo.

```mermaid
flowchart TD
    U["Choix utilisateur<br/>utilisateurs.json"] --> L["Lieu de départ<br/>Lieu d'arrivée"]
    L --> P1["station_conseillee(besoin='velo',<br/>type_velo = ⚡ / 🚲 / peu importe)"]
    L --> P2["station_conseillee(besoin='borne')"]
    P1 & P2 --> F["Filtre : en service et<br/>au moins 1 vélo du bon type / 1 borne libre"]
    F --> D["distance_m() : formule de haversine"]
    D --> S["Tri : la plus proche,<br/>à égalité celle qui en a le plus"]
    S --> R(["📍 Station de départ + station d'arrivée<br/>+ stations dans un rayon de 500 m"])
```

---

## 9. Bonus : la pluie fait-elle fuir les cyclistes ?

L'API ne donne pas les trajets, seulement l'état des stations. Nous mesurons donc l'effet **indirectement** :
moins de cyclistes = stations **plus pleines** ; électriques préférés sous la pluie = **moins d'électriques** en station.

```mermaid
sequenceDiagram
    autonumber
    participant B as collecter.py
    participant V as API Vélib
    participant M as Météo-France
    participant H as releves.csv
    participant A as app.py (onglet 🌧️)

    loop toutes les 15 minutes
        B->>V: telecharger_velib()
        V-->>B: état des stations
        B->>M: meteo_actuelle()
        M-->>B: température, vent, pluie
        B->>H: une ligne par zone (stats + météo)
    end
    A->>H: lire_historique()
    A->>A: compare pluie / sec<br/>à heure égale (semaine / week-end)
    A-->>A: conclusion() en français
```

**Piège évité** : la pluie et les heures de pointe se mélangent. On compare donc les relevés
**au même créneau horaire**. Collecte lancée le 8 novembre 2026 ; conclusion après quelques jours de pluie.

---

## 10. Organisation de l'équipe

```mermaid
flowchart LR
    subgraph A["👤 A — Données"]
        A1[recuperation.py]
        A2[nettoyage.py]
    end
    subgraph B["👤 B — Calculs"]
        B1[indicateurs.py]
        B2[comparaison.py]
        B3[compare.py]
    end
    subgraph C["👤 C — Interface"]
        C1[meteo.py]
        C2[app.py]
    end
    K{{"📜 Contrat — issue #4<br/>noms des colonnes<br/>signatures des fonctions"}}
    A -->|tableau nettoyé| K
    K -->|colonnes garanties| B
    K -->|colonnes garanties| C
    B -->|dict de stats| C
```

- **Le contrat d'abord** : tout le monde a pu coder en parallèle dès le jour 1, sur de fausses données (`tests/donnees_test.csv`).
- **Une branche et une PR par tâche** : `main` marche toujours.
- **`RELAIS.md`** : le journal des décisions et de l'avancement.
- **78 tests `pytest`** : nettoyage, indicateurs, comparaison, météo, trajet, erreurs, collecte.

---

## 11. Démonstration

```bash
python compare.py "Paris 11" Montreuil     # duel dans le terminal
python compare.py montreuill Paris         # faute de frappe → suggestion
streamlit run app.py                       # appli web : duel, trajet, carte, météo
python collecter.py --une-fois             # un relevé dans l'historique
pytest                                     # 78 tests
```

---

## 12. Bilan et pistes

**Ce qu'on a appris**
- Les données réelles sont sales : nettoyer prend autant de temps que calculer.
- Un contrat écrit évite les conflits entre membres de l'équipe.
- Prévoir la panne (API, clé absente, faute de frappe) fait la différence en démonstration.

**Pistes**
- Conclure l'analyse météo après plusieurs semaines de collecte.
- Prédire le remplissage d'une station à une heure donnée.
- Station de secours dans « Mon trajet » si la première se vide en chemin.

**Merci ! Questions ?**

# LotteryPrediction

Application web Flask pour consulter l'historique des tirages Loto et EuroMillions et générer des propositions de grilles basées sur plusieurs méthodes statistiques simples.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Initialisation de la base de données

Au premier lancement, l'application crée automatiquement une base SQLite dans `data/lottery.db`. Cliquez sur « Mettre à jour les données » depuis l'interface ou exécutez le script suivant pour télécharger l'historique complet :

```bash
python -m app.scripts.update_data
```

## Lancement du serveur de développement

```bash
flask --app app run --reload
```

Ensuite ouvrez http://127.0.0.1:5000/ dans votre navigateur.

## Structure des prédictions

Trois méthodes sont proposées pour chaque jeu :

1. **Fréquence historique** – sélectionne les numéros les plus fréquemment tirés sur l'ensemble de l'historique.
2. **Tendance récente** – se concentre sur les tirages des dernières semaines (30 tirages) pour détecter des numéros « chauds ».
3. **Évitement du dernier tirage** – construit une grille aléatoire en excluant les numéros du dernier tirage pour varier les combinaisons.

Les prédictions sont générées dynamiquement à chaque affichage de la page d'accueil.

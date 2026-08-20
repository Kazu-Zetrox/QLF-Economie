# Bot économie QLF

Installation rapide (Windows) :

1. Crée un environnement virtuel et active-le :

```bash
python -m venv venv
venv\Scripts\activate
```

2. Installer dépendances :

```bash
pip install -r requirements.txt
```

3. Méthode recommandée : crée un fichier `.env` à la racine du projet (voie persistante).

	- Copie `.env.example` en `.env` et remplace la valeur :

	```text
	DISCORD_TOKEN=TON_NOUVEAU_TOKEN
	```

	- Ou temporaire (CMD) :

	```bat
	set DISCORD_TOKEN=TON_NOUVEAU_TOKEN
	python bot.py
	```

4. Lancer :

```bash
python bot.py
```

Commandes disponibles :
- `!work` — gagne de l'argent (cooldown 10min)
- `!slut` — gamble, 1/3 chance de perdre (cooldown 15min)
- `!bank all` — déposer tout l'argent sur toi dans la banque
- `!deposit <montant>` — déposer une somme précise à la banque
- `!deposer <montant>` — alias français de `!deposit`
- `!withdraw <montant>` — retirer de la banque
- `!withdraw all` — retirer tout l'argent de la banque
- `!pay @membre <montant>` — donner de l'argent liquide à un membre
- `!donner @membre <montant>` — alias français de `!pay`
- `!daily` — récupérer $250 chaque jour
- `!weekly` — récupérer $1,500 chaque semaine
- `!crime` ou `!crim` — tenter un crime, avec une chance de jackpot (cooldown 20min)
- `!steal @membre` — voler 20 à 50 % de l'argent liquide après 5h de protection (l'argent en banque est toujours protégé)
- `!ping` — vérifier que le bot répond
- `!profile` — voir ton profil économique
- `!achievements` — voir tes achievements
- `!shop` — voir les thèmes et effets disponibles
- `!inventory` — voir tous tes objets possédés
- `!buy <objet>` — acheter un objet de profil
- `!equip <objet>` — équiper un objet acheté
- `!setvideo <lien Tenor ou .mp4>` — ajouter une vidéo personnalisée au profil
- Joindre directement une vidéo au message `!setvideo` — l'afficher dans `!profile`
- `!setvideo off` — retirer sa vidéo personnalisée
- `!leaderboard` — voir la richesse des membres du serveur
- `!help` — afficher toutes les commandes
- `!blackjack <mise>` — jouer et gagner ou perdre la mise (cooldown 10min)

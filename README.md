# AI Agent for Business Intelligence

Application Business Intelligence permettant de poser des questions en langage
naturel sur des données de ventes. L'utilisateur accède à une application
mobile React Native / Expo, protégée par JWT, qui communique avec une API
FastAPI. Cette API orchestre plusieurs agents spécialisés pour interroger
PostgreSQL, calculer des indicateurs, produire des prévisions et rédiger des
synthèses.

> Projet académique réalisé pour une démonstration technique / rapport de
> stage. La démo principale est locale : PC Windows + PostgreSQL + Ollama +
> application Expo.

## Fonctionnalités

- Inscription, connexion, restauration de session et déconnexion.
- Authentification JWT et protection des routes mobile et API.
- Assistant conversationnel BI connecté à FastAPI et PostgreSQL.
- Dashboard avec ventes totales, profit total et ventes mensuelles réelles.
- Rapports BI textuels construits avec les données réelles disponibles.
- Prévisions de ventes grâce à un modèle LSTM local.
- Gestion d'erreurs réseau, de JWT expiré et de temps de réponse Ollama élevé.

## Architecture

```text
React Native / Expo
        ↓
FastAPI + JWT
        ↓
Orchestrator
        ↓
┌────────────┬─────────────┬──────────────┬─────────────┐
│ SQL Agent  │ Analytics   │ Forecast     │ Report      │
│            │ Agent       │ Agent        │ Agent       │
└────────────┴─────────────┴──────────────┴─────────────┘
        ↓
PostgreSQL / Ollama llama3.1 / LSTM
```

| Couche | Rôle |
| --- | --- |
| Application mobile | Login, Dashboard, Chat, Reports et navigation protégée. |
| FastAPI | API REST, authentification, validation des requêtes et routes protégées. |
| Orchestrator | Sélectionne et enchaîne les agents nécessaires à une question BI. |
| Agents | Génèrent SQL, KPI, prévisions ou synthèses selon la demande. |
| PostgreSQL | Stocke les utilisateurs et les données BI du schéma en étoile. |
| Ollama | Exécute localement le modèle `llama3.1` pour le routage, le SQL et les rapports. |
| LSTM | Produit des prévisions de ventes à partir de données historiques. |

## Technologies

- **Mobile** : React Native, Expo SDK 57, Expo Router, TypeScript, Axios,
  Expo SecureStore.
- **Backend** : Python, FastAPI, Pydantic, SQLAlchemy, python-jose, passlib.
- **Données** : PostgreSQL, pandas, psycopg2.
- **IA** : Ollama, `llama3.1`, TensorFlow / Keras, scikit-learn, joblib.
- **Tests** : pytest et unittest.mock.

## Structure du projet

```text
AI_BI/
├── backend/                 # FastAPI, JWT, configuration et routeurs
│   ├── core/                # config, sécurité JWT et dépendances
│   ├── db/                  # connexion PostgreSQL
│   ├── models/              # schémas Pydantic
│   ├── routers/             # auth, chat, data et agents
│   └── .env.example         # modèle de configuration backend
├── mobile/                  # application React Native / Expo Router
│   ├── src/app/             # Login, Register, Home, Chat, Dashboard, Reports
│   ├── src/contexts/        # AuthContext
│   ├── src/services/        # client API Axios
│   └── .env.example         # modèle de configuration mobile
├── models/                  # artefacts LSTM nécessaires au runtime
├── tests/                   # tests unitaires Python
├── Orchestrator.py
├── sql_agent.py
├── analytics_agent.py
├── forecast_agent.py
├── report_agent.py
├── README_DEMO.md           # procédure de démonstration Expo Go locale
└── README.md
```

## Prérequis

- Python 3.11 ou compatible.
- PostgreSQL avec la base BI initialisée.
- Node.js et npm.
- Ollama installé localement.
- Modèle Ollama `llama3.1` téléchargé.
- Expo Go uniquement si vous souhaitez tester sur téléphone.

## Installation

Depuis la racine du projet, créez et activez l'environnement Python :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Installez ensuite les dépendances mobile :

```powershell
cd mobile
npm.cmd install
```

Téléchargez le modèle local une seule fois :

```powershell
ollama pull llama3.1
ollama list
```

## Configuration

Les fichiers `.env` sont privés et ne doivent jamais être versionnés ni
partagés. Des modèles sans secret sont fournis.

```powershell
# Depuis la racine du projet
Copy-Item backend\.env.example backend\.env
Copy-Item mobile\.env.example mobile\.env
```

### Backend : `backend/.env`

Renseignez vos valeurs locales dans ce fichier privé :

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nom_de_votre_base
DB_USER=votre_utilisateur_postgresql
DB_PASSWORD=votre_mot_de_passe_postgresql

JWT_SECRET_KEY=une_longue_cle_aleatoire_non_partagee
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

CORS_ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
MODEL_DIR=models
```

`JWT_SECRET_KEY` est obligatoire : le backend refuse de démarrer si cette
variable est absente.

### Mobile : `mobile/.env`

Pour le navigateur web sur le même PC :

```env
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000
```

Pour Expo Go sur téléphone, utilisez l'adresse IPv4 locale actuelle du PC :

```env
EXPO_PUBLIC_API_URL=http://VOTRE_IP_LOCALE_DU_PC:8000
```

Ne placez jamais de mot de passe, clé JWT ou autre secret dans une variable
`EXPO_PUBLIC_*` : ces variables sont visibles côté application mobile.

## Lancement local

Vérifiez d'abord qu'Ollama est disponible :

```powershell
ollama list
```

Dans un premier terminal, depuis la racine du projet, démarrez FastAPI :

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

La documentation Swagger est disponible sur :

```text
http://127.0.0.1:8000/docs
```

Dans un second terminal, démarrez l'application Expo Web :

```powershell
cd mobile
npm.cmd run web
```

Pour Expo Go sur le réseau local :

```powershell
cd mobile
npm.cmd run start -- --lan
```

La procédure détaillée de démonstration téléphone est disponible dans
[`README_DEMO.md`](README_DEMO.md).

## Agents IA

### SQL Agent

Transforme une question BI en requête SQL PostgreSQL, valide les tables
autorisées, exécute la requête et retourne des résultats structurés. Les
résultats SQL simples sont formatés de façon déterministe, sans appel LLM
final inutile.

### Analytics Agent

Calcule des indicateurs BI : marge, croissance des ventes, panier moyen et
remise moyenne. Il applique les filtres compatibles, notamment par catégorie
ou période.

### Forecast Agent

Utilise le modèle `lstm_sales_forecast.keras`, le scaler et la liste de
colonnes pour prédire les ventes futures. Les trois artefacts sont chargés
depuis `MODEL_DIR`.

### Report Agent

Produit une synthèse avec un titre, un résumé et des points clés à partir des
données fournies par les agents producteurs. Ses instructions empêchent
l'invention de chiffres ou de comparaisons non démontrées.

### Orchestrator

Analyse la demande, appelle l'agent approprié et retourne une réponse lisible.
Pour une demande de rapport explicite, il collecte d'abord des données SQL,
Analytics ou Forecast, puis appelle le Report Agent avec ce contexte réel.

## API principale

| Méthode | Route | Authentification | Utilité |
| --- | --- | --- | --- |
| POST | `/auth/register` | Non | Créer un compte. |
| POST | `/auth/login` | Non | Obtenir un JWT. |
| POST | `/chat` | JWT | Poser une question BI à l'Orchestrator. |
| GET | `/data/kpis/summary` | JWT | Récupérer les KPI globaux. |
| GET | `/data/sales/timeseries` | JWT | Récupérer les ventes mensuelles. |
| GET | `/data/categories` | JWT | Récupérer les catégories disponibles. |
| GET | `/data/regions` | JWT | Récupérer les régions disponibles. |
| POST | `/agents/sql` | JWT | Appeler directement le SQL Agent. |
| POST | `/agents/analytics` | JWT | Appeler directement l'Analytics Agent. |
| POST | `/agents/forecast` | JWT | Appeler directement le Forecast Agent. |
| POST | `/agents/report` | JWT | Générer un rapport à partir de résultats BI. |

Les routes protégées attendent :

```text
Authorization: Bearer <access_token>
```

## Application mobile

Le parcours principal est le suivant :

```text
Login / Register
        ↓
Home
 ├── Assistant BI → Chat
 ├── Dashboard BI → KPI + ventes mensuelles
 └── Rapports BI → synthèse textuelle
        ↓
Logout → Login
```

Le token JWT est stocké avec Expo SecureStore sur Android/iOS. Un fallback
localStorage est utilisé uniquement pour faciliter les tests dans le navigateur
web. Les utilisateurs non authentifiés sont redirigés vers Login.

## Exemples de questions BI

### SQL

- `Quel est le total des ventes ?`
- `Quel produit est le plus vendu ?`
- `Quelles sont les ventes par région ?`
- `Quelles sont les 3 catégories avec le plus de ventes ?`

### Analytics

- `Quel est le panier moyen ?`
- `Quel est le taux de croissance des ventes en 2013 ?`
- `Quelle est la marge sur la catégorie Technology ?`
- `Quel est le taux de remise moyen pour Furniture ?`

### Forecast

- `Prévois les ventes pour les 7 prochains jours.`
- `Quelle sera la prévision des ventes pour les 3 prochains mois ?`
- `Prévois les ventes Technology pour le mois prochain.`

### Report

- `Fais-moi un rapport sur le produit le plus vendu au total.`
- `Donne-moi un résumé de la marge sur la catégorie Furniture.`

## Tests et validation

Exécutez les tests unitaires depuis la racine :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v
```

Résultat final validé : **25/25 tests unitaires réussis**.

Vérifiez TypeScript depuis `mobile/` :

```powershell
.\node_modules\.bin\tsc.cmd --noEmit
```

Résultat final validé : aucune erreur TypeScript.

## Démonstration et limites connues

La démonstration locale Web a été validée : authentification, Chat, Dashboard,
Reports, Logout, FastAPI et PostgreSQL fonctionnent ensemble.

- Ollama `llama3.1` s'exécute localement sur CPU et certaines requêtes peuvent
  être lentes.
- Aucun déploiement cloud n'a été effectué : le projet est préparé pour une
  démonstration locale sur PC.
- La préparation Expo Go est terminée, mais le **test réel sur téléphone est
  volontairement reporté**. Il ne doit pas être présenté comme validé.

## Évolutions possibles

- Déployer le backend sur une VM adaptée à Ollama et TensorFlow.
- Ajouter un GPU ou un modèle plus léger pour réduire la latence.
- Mettre en place Docker et un pipeline CI.
- Ajouter l'historique des conversations, des filtres Dashboard avancés et
  l'export PDF des rapports.
- Automatiser des tests d'intégration complets et valider Expo Go sur téléphone.

## Sécurité et fichiers locaux

Le fichier `.gitignore` exclut notamment les fichiers `.env`, les environnements
virtuels, `node_modules`, les caches Python/Expo et les journaux. Les artefacts
LSTM présents dans `models/` restent nécessaires à l'exécution du Forecast
Agent et ne doivent pas être exclus.

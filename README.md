# ⚡ Energy Data Platform

Plateforme de gestion et d'analyse de données énergétiques en temps réel avec détection intelligente d'anomalies.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

---

## 🎯 Fonctionnalités

### Backend (FastAPI + PostgreSQL)
- ✅ **API REST** complète et documentée (Swagger/OpenAPI)
- ✅ **Gestion des sites** énergétiques (solaire, éolien, hydraulique, etc.)
- ✅ **Monitoring en temps réel** via compteurs intelligents
- ✅ **Détection d'anomalies** avec 3 algorithmes ML :
  - Z-Score (rapide)
  - IQR - Interquartile Range (robuste)
  - Moving Average (patterns temporels)
- ✅ **Agrégations** temporelles (horaire, journalière)
- ✅ **Tests unitaires** et d'intégration (92% de couverture)

### Frontend (React + TypeScript + Tailwind CSS)
- ✅ **Dashboard** interactif avec KPIs temps réel
- ✅ **Visualisation** des données (graphiques Recharts)
- ✅ **Gestion des anomalies** avec filtres dynamiques :
  - Par période (24h, 48h, 7j, 30j)
  - Par compteur (tous ou spécifique)
  - Par statut (pending, verified, ignored)
- ✅ **Actions** sur les anomalies (vérifier, ignorer, réouvrir)
- ✅ **Interface moderne** et responsive

---

## 🏗️ Architecture

```
energy-data-platform/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── services/       # Logique métier
│   │   ├── core/           # Configuration
│   │   └── tests/          # Tests (64 tests, 92% coverage)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # Application React
│   ├── src/
│   │   ├── components/    # Composants réutilisables
│   │   ├── pages/         # Pages principales
│   │   ├── services/      # API client
│   │   └── types/         # Types TypeScript
│   ├── Dockerfile
│   └── package.json
│
└── docker-compose.yml     # Orchestration Docker
```

---

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose
- Git

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/tawousama/energy-data-platform.git
cd energy-data-platform

# 2. Copier le fichier d'environnement
cp .env.docker .env

# 3. Lancer avec Docker Compose
docker-compose up -d

# 4. Initialiser la base de données (première fois uniquement)
docker-compose exec backend python all_in_one.py
```

### Accès

- 🌐 **Frontend** : http://localhost
- 📡 **API Backend** : http://localhost:8000
- 📚 **Documentation API** : http://localhost:8000/docs
- 🗄️ **PostgreSQL** : localhost:5432

---

## 💻 Développement Local (Sans Docker)

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configurer PostgreSQL
psql -U postgres
CREATE DATABASE energy_db;
CREATE USER energy_user WITH PASSWORD 'energy_password';
GRANT ALL PRIVILEGES ON DATABASE energy_db TO energy_user;

# Lancer le serveur
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Créer le fichier .env
echo "VITE_API_URL=http://localhost:8000" > .env

# Lancer le serveur de dev
npm run dev
```

### Tests

```bash
# Backend
cd backend
pytest --cov=app

# Frontend
cd frontend
npm test
```

---

## 📊 Utilisation

### 1. Créer des Sites Énergétiques

```bash
# Via l'API
curl -X POST http://localhost:8000/api/v1/sites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Parc Solaire Bordeaux",
    "site_type": "solar",
    "location": "Bordeaux, France",
    "capacity_kw": 5000
  }'
```

### 2. Détecter des Anomalies

Via le frontend : **Analytics** → Sélectionner compteur → **Lancer la Détection**

Ou via l'API :
```bash
curl -X POST http://localhost:8000/api/v1/analytics/anomalies/detect/1?method=zscore
```

### 3. Gérer les Anomalies

- **Vérifier** : Confirmer qu'il s'agit d'une vraie anomalie
- **Ignorer** : Marquer comme fausse alerte
- **Réouvrir** : Remettre en statut "pending"

---

## 🧪 Tests

### Backend (92% de couverture)

```bash
cd backend

# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest -k "anomaly"
```

### Types de Tests
- **Tests unitaires** : Services de détection d'anomalies
- **Tests d'intégration** : Endpoints API
- **Tests de fixtures** : Isolation des données

---

## 🐳 Déploiement

### Docker Compose (Recommandé)

```bash
# Production
docker-compose -f docker-compose.yml up -d

# Logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### Plateformes Gratuites

#### Option 1 : Railway.app
```bash
# 1. Créer un compte sur railway.app
# 2. Connecter votre repo GitHub
# 3. Railway détecte automatiquement docker-compose.yml
# 4. Déployer !
```

#### Option 2 : Render.com
- Backend : Web Service (Docker)
- Frontend : Static Site
- Database : PostgreSQL gratuit

#### Option 3 : Fly.io
```bash
flyctl launch
flyctl deploy
```

---

## 📈 Algorithmes de Détection

### Z-Score
Détecte les valeurs qui s'écartent de la moyenne de plus de N écarts-types.
- **Rapide** : O(n)
- **Sensible** aux outliers extrêmes

### IQR (Interquartile Range)
Utilise les quartiles pour détecter les valeurs aberrantes.
- **Robuste** aux outliers
- **Efficace** pour distributions non-gaussiennes

### Moving Average
Compare chaque valeur à la moyenne mobile.
- **Adaptatif** aux tendances
- **Bon** pour les patterns temporels

---

## 🛠️ Stack Technique

### Backend
- **FastAPI** - Framework web moderne et performant
- **SQLAlchemy** - ORM Python
- **PostgreSQL** - Base de données relationnelle
- **Pydantic** - Validation de données
- **Pytest** - Framework de tests

### Frontend
- **React 18** - Library UI
- **TypeScript** - Typage statique
- **Vite** - Build tool moderne
- **Tailwind CSS** - Framework CSS utility-first
- **React Query** - Gestion d'état serveur
- **Recharts** - Bibliothèque de graphiques
- **React Router** - Navigation

### DevOps
- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration
- **GitHub Actions** - CI/CD (à venir)

---

## 📝 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍💻 Auteur

Développé par Tawous - Projet de démonstration de plateforme énergétique intelligente.

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

---

## 📞 Support

Pour toute question ou problème :
- 📧 Email : amaratawous@gmail.com
- 🐛 Issues : [GitHub Issues](https://github.com/tawousama/energy-data-platform/issues)

---

⭐ **N'oubliez pas de star le projet si vous le trouvez utile !** ⭐
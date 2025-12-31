# 🎬 Système de Recommandation de Films sur GCP

**Projet Cloud Computing - Master AI**  
**Auteurs :** Mamadi Keita & Skander  
**Date :** Décembre 2025

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Choix Techniques](#choix-techniques)
- [Dataset](#dataset)
- [Installation et Utilisation](#installation-et-utilisation)
- [Résultats](#résultats)
- [Déploiement](#déploiement)
- [Structure du Projet](#structure-du-projet)

---

## 🎯 Vue d'ensemble

Ce projet implémente un **système de recommandation de films personnalisé** déployé sur Google Cloud Platform (GCP). Le système utilise une approche hybride combinant filtrage collaboratif et recommandations basées sur le contenu pour s'adapter dynamiquement aux nouveaux utilisateurs et évoluer avec leurs préférences.

### Fonctionnalités principales

✅ **Recommandations personnalisées** basées sur l'historique de l'utilisateur  
✅ **Cold-start handling** pour les nouveaux utilisateurs sans historique  
✅ **Système hybride** qui s'adapte au nombre de notes disponibles  
✅ **API REST** déployable sur Cloud Run  
✅ **Architecture cloud-native** avec BigQuery et Cloud Storage

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    VERTEX AI WORKBENCH                      │
│                  (Développement & Entraînement)             │
│                                                              │
│  📓 Notebooks  →  🧪 EDA  →  🧹 Cleaning  →  🤖 Modèle     │
└──────────────┬───────────────────────┬──────────────────────┘
               │                       │
               ↓                       ↓
    ┌──────────────────┐    ┌──────────────────┐
    │    BIGQUERY      │    │  LOCAL STORAGE   │
    │                  │    │  (.pkl files)    │
    │ • movies_clean   │    │                  │
    │ • ratings_clean  │    │ • Modèle entraîné│
    └────────┬─────────┘    └─────────┬────────┘
             │                        │
             └────────┬───────────────┘
                      ↓
            ┌──────────────────┐
            │    CLOUD RUN     │
            │   (API Flask)    │
            │                  │
            │   🌐 Public API  │
            └──────────────────┘
```

---

## 🧠 Choix Techniques

### 1. **Approche Hybride de Recommandation**

**Pourquoi ?**
- Les systèmes purement collaboratifs échouent sur les nouveaux utilisateurs (cold-start problem)
- Les systèmes basés uniquement sur le contenu manquent de personnalisation
- Notre approche combine les deux pour le meilleur résultat

**Comment ça fonctionne ?**

| Nombre de notes | Stratégie | Justification |
|-----------------|-----------|---------------|
| **0 notes** | Content-based (genres + popularité) | Recommande les films les plus populaires dans les genres préférés |
| **1-4 notes** | Hybride (50% collaboratif + 50% contenu) | Commence à personnaliser tout en gardant des suggestions populaires |
| **5+ notes** | Collaborative filtering (similarité cosinus) | Recommandations entièrement personnalisées basées sur des utilisateurs similaires |

### 2. **Nettoyage des Données**

**Décisions prises :**

| Action | Raison |
|--------|--------|
| Supprimer films avec < 5 notes | Pas assez de données pour des recommandations fiables |
| Supprimer utilisateurs avec < 10 notes | Impossible de calculer des similarités précises |
| Supprimer films sans genre | Nécessaire pour le content-based filtering |

**Impact :**
- **Avant :** 10,329 films, 105,339 ratings
- **Après :** 3,855 films, 94,121 ratings (89.4% conservés !)
- **Densité de la matrice :** 1.53% → 3.65% (amélioration de 2.4×)

### 3. **Métriques d'Évaluation**

**Choix de RMSE et MAE :**
- **RMSE** : Pénalise fortement les grandes erreurs
- **MAE** : Plus robuste aux outliers, interprétation intuitive

**Train/Test Split :**
- 80% entraînement, 20% test
- Permet de détecter l'overfitting
- Validation scientifique des performances

### 4. **Architecture Cloud-Native**

**BigQuery pour les données :**
- ✅ Scalable (fonctionne avec des milliards de lignes)
- ✅ Requêtes SQL rapides
- ✅ Séparation données/code (bonne pratique)

**Flask + Gunicorn pour l'API :**
- ✅ Léger et rapide
- ✅ Production-ready avec Gunicorn
- ✅ Facile à containeriser avec Docker

---

## 📊 Dataset

**Source :** BigQuery `master-ai-cloud.MoviePlatform`

### Statistiques (après nettoyage)

| Métrique | Valeur |
|----------|--------|
| **Films** | 3,855 |
| **Ratings** | 94,121 |
| **Utilisateurs** | 668 |
| **Note moyenne** | 3.57 / 5.0 |
| **Genres** | 19 (Action, Comedy, Drama, etc.) |
| **Densité de la matrice** | 3.65% |

### Distributions

- **Notes les plus fréquentes :** 4.0, 3.5, 4.5
- **Films les plus notés :** Pulp Fiction (325), Forrest Gump (311), Shawshank Redemption (308)
- **Utilisateurs très actifs :** Max 200+ notes

---

## 🚀 Installation et Utilisation

### Prérequis

- Python 3.10+
- Compte GCP avec accès au projet `students-group1`
- Git

### 1. Cloner le Repository
```bash
git clone https://github.com/keita223/movie-recommendation-gcp.git
cd movie-recommendation-gcp
```

### 2. Explorer les Notebooks

**Dans Vertex AI Workbench :**
```bash
# Ouvrir JupyterLab
# Naviguez vers notebooks/

# 1. Analyse exploratoire
notebooks/01_exploratory_data_analysis.ipynb

# 2. Nettoyage des données
notebooks/data_cleaning.ipynb

# 3. Modèle de recommandation
notebooks/02_recommendation_model.ipynb

# 4. Évaluation
notebooks/03_model_evaluation.ipynb
```

### 3. Tester l'API en Local
```bash
cd deployment

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
python app.py
```

**L'API démarre sur `http://localhost:5000`**

### 4. Tester les Endpoints

**Health Check :**
```bash
curl http://localhost:5000/health
```

**Recommandations pour nouveau (genres préférés) :**
```bash
curl -X POST http://localhost:5000/recommend/new \
  -H "Content-Type: application/json" \
  -d '{"genres": ["Action", "Sci-Fi"], "n": 5}'
```

**Recommandations personnalisées (basées sur notes) :**
```bash
curl -X POST http://localhost:5000/recommend/personalized \
  -H "Content-Type: application/json" \
  -d '{
    "ratings": {
      "296": 5.0,
      "318": 4.5,
      "260": 4.0
    },
    "n": 5
  }'
```

**Recherche de films :**
```bash
curl "http://localhost:5000/search?q=matrix&limit=5"
```

**Liste des genres :**
```bash
curl http://localhost:5000/genres
```

---

## 📈 Résultats

### Métriques de Performance

| Métrique | Train | Test | Baseline | Amélioration |
|----------|-------|------|----------|--------------|
| **RMSE** | 0.9892 | 1.0344 | 1.0320 | -0.2% |
| **MAE** | 0.7621 | 0.8142 | 0.8322 | **+2.2%** |

### Analyse

✅ **Pas d'overfitting** : Différence train/test de seulement 6.8% (< 10%)  
✅ **Généralisation correcte** : Le modèle performe bien sur données non vues  
✅ **Comparable au baseline** : Performance similaire en termes de métriques brutes  
⭐ **Avantage principal** : **Personnalisation** - recommandations adaptées à chaque utilisateur

### Interprétation

Le modèle obtient des performances comparables à un baseline qui prédit toujours la moyenne. **Cependant**, l'avantage crucial est la **personnalisation** :

- Le baseline recommande toujours les mêmes films populaires
- Notre modèle adapte les recommandations à chaque utilisateur
- Sur un dataset sparse (3.65% de densité), c'est un résultat attendu et acceptable

### Graphiques Générés

📊 `train_test_comparison.png` - Comparaison des métriques  
📊 `predictions_analysis.png` - Analyse des prédictions  
📊 `error_distribution.png` - Distribution des erreurs

---

## ☁️ Déploiement

### Build Docker Local
```bash
cd deployment
docker build -t movie-recommender .
docker run -p 8080:8080 movie-recommender
```

### Déploiement sur Cloud Run

**Prérequis :** APIs Cloud Build et Cloud Run activées
```bash
gcloud run deploy movie-recommender-api \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300 \
  --project students-group1
```

**Note :** Actuellement en attente d'activation des permissions pour le groupe 1.

---

## 📁 Structure du Projet
```
movie-recommendation-gcp/
│
├── notebooks/                                  # Jupyter notebooks
│   ├── 01_exploratory_data_analysis.ipynb     # EDA complète
│   ├── data_cleaning.ipynb                    # Nettoyage des données
│   ├── 02_recommendation_model.ipynb          # Modèle de recommandation
│   └── 03_model_evaluation.ipynb              # Évaluation train/test
│
├── scripts/                                    # Scripts Python
│   ├── recommender.py                         # Classe MovieRecommender
│   └── test_recommender.py                    # Tests unitaires
│
├── models/                                     # Modèles entraînés (.pkl)
│   ├── df_movies_clean.pkl                    # Films nettoyés
│   ├── df_ratings_clean.pkl                   # Ratings nettoyés
│   ├── user_movie_matrix.pkl                  # Matrice utilisateur-film
│   ├── genres_df.pkl                          # Matrice des genres
│   └── mlb.pkl                                # MultiLabelBinarizer
│
├── deployment/                                 # Configuration déploiement
│   ├── app.py                                 # API Flask
│   ├── Dockerfile                             # Configuration Docker
│   ├── requirements.txt                       # Dépendances Python
│   └── models/                                # Modèles (copie pour Docker)
│
├── data/                                       # Données (ignorées par Git)
├── docs/                                       # Documentation
└── README.md                                   # Ce fichier
```

---

## 🛠️ Technologies Utilisées

| Catégorie | Technologies |
|-----------|--------------|
| **Cloud Platform** | Google Cloud Platform (GCP) |
| **Data Storage** | BigQuery, Cloud Storage |
| **Compute** | Vertex AI Workbench, Cloud Run |
| **ML/Data** | pandas, numpy, scikit-learn |
| **API** | Flask, Gunicorn |
| **Containerization** | Docker |
| **Version Control** | Git, GitHub |

---

## 📝 Améliorations Futures

1. **Modèle plus sophistiqué** : Matrix Factorization (SVD, ALS), Deep Learning (Neural Collaborative Filtering)
2. **Features supplémentaires** : Acteurs, réalisateurs, année de sortie, tags utilisateurs
3. **Système de feedback** : Collecter les retours utilisateurs pour améliorer le modèle
4. **A/B Testing** : Tester différentes stratégies de recommandation
5. **Interface utilisateur** : Développer un frontend web interactif
6. **Cloud Storage** : Migrer les modèles vers Google Cloud Storage (actuellement limité par permissions)

---

## 👥 Contributeurs

- **Mamadi Keita** - Development, ML, Deployment
- **Skander** - Development, ML, Documentation

---

## 📄 Licence

Projet académique - Master AI Cloud Computing

---

## 🙏 Remerciements

- **Mr Doré** - profeseur IA on the cloud

---

** Si vous trouvez ce projet utile, n'hésitez pas à le star sur GitHub !**
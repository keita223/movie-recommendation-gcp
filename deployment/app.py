from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

app = Flask(__name__)

# Variables globales pour le modèle
df_movies = None
df_ratings = None
user_movie_matrix = None
mlb = None

def load_model():
    """Charger le modèle et les données au démarrage"""
    global df_movies, df_ratings, user_movie_matrix, mlb
    
    print("🔄 Chargement du modèle...")
    
    # Chemin vers les fichiers (relatif ou absolu)
    models_path = '../models'
    if not os.path.exists(models_path):
        models_path = './models'  # Pour Docker
    
    df_movies = pd.read_pickle(f'{models_path}/df_movies_clean.pkl')
    df_ratings = pd.read_pickle(f'{models_path}/df_ratings_clean.pkl')
    user_movie_matrix = pd.read_pickle(f'{models_path}/user_movie_matrix.pkl')
    
    with open(f'{models_path}/mlb.pkl', 'rb') as f:
        mlb = pickle.load(f)
    
    print(f"✅ Modèle chargé : {len(df_movies)} films, {len(df_ratings)} ratings")

def recommend_for_new_user(preferred_genres=None, n_recommendations=10):
    """Recommandations pour nouveaux utilisateurs"""
    movie_popularity = df_ratings.groupby('movieId').agg({
        'rating': ['count', 'mean']
    }).reset_index()
    movie_popularity.columns = ['movieId', 'num_ratings', 'avg_rating']
    
    recommendations = df_movies.merge(movie_popularity, on='movieId', how='left')
    recommendations['num_ratings'] = recommendations['num_ratings'].fillna(0)
    recommendations['avg_rating'] = recommendations['avg_rating'].fillna(0)
    
    if preferred_genres:
        mask = recommendations['genres_list'].apply(
            lambda x: any(genre in x for genre in preferred_genres)
        )
        recommendations = recommendations[mask]
    
    recommendations = recommendations[recommendations['num_ratings'] >= 20]
    
    recommendations['score'] = (
        recommendations['num_ratings'] * 0.3 + 
        recommendations['avg_rating'] * 100 * 0.7
    )
    
    recommendations = recommendations.sort_values('score', ascending=False)
    
    return recommendations[['movieId', 'title', 'genres', 'avg_rating']].head(n_recommendations)

def recommend_based_on_ratings(user_ratings, n_recommendations=10, n_similar_users=20):
    """Recommandations basées sur les notes de l'utilisateur"""
    new_user_vector = pd.Series(0, index=user_movie_matrix.columns)
    
    for movie_id, rating in user_ratings.items():
        if movie_id in new_user_vector.index:
            new_user_vector[movie_id] = rating
    
    similarities = cosine_similarity(
        [new_user_vector.values],
        user_movie_matrix.values
    )[0]
    
    similar_users_idx = np.argsort(similarities)[::-1][:n_similar_users]
    similar_users = user_movie_matrix.iloc[similar_users_idx]
    
    weights = similarities[similar_users_idx]
    weighted_ratings = similar_users.T.dot(weights) / weights.sum()
    
    already_rated = list(user_ratings.keys())
    weighted_ratings = weighted_ratings.drop(already_rated, errors='ignore')
    
    top_movies = weighted_ratings.sort_values(ascending=False).head(n_recommendations)
    
    recommendations = df_movies[df_movies['movieId'].isin(top_movies.index)].copy()
    recommendations['predicted_rating'] = recommendations['movieId'].map(top_movies)
    recommendations = recommendations.sort_values('predicted_rating', ascending=False)
    
    return recommendations[['movieId', 'title', 'genres', 'predicted_rating']]

@app.route('/')
def home():
    """Page d'accueil"""
    return jsonify({
        'message': 'API de recommandation de films',
        'version': '1.0',
        'endpoints': {
            '/health': 'Vérifier la santé de l\'API',
            '/recommend/new': 'Recommandations pour nouveaux utilisateurs',
            '/recommend/personalized': 'Recommandations personnalisées',
            '/search': 'Rechercher des films'
        }
    })

@app.route('/health')
def health():
    """Endpoint de santé"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': df_movies is not None,
        'num_movies': len(df_movies) if df_movies is not None else 0
    })

@app.route('/recommend/new', methods=['POST'])
def recommend_new():
    """Recommandations pour nouveaux utilisateurs
    
    Body JSON:
    {
        "genres": ["Action", "Sci-Fi"],  # Optionnel
        "n": 10  # Optionnel (défaut: 10)
    }
    """
    data = request.get_json()
    
    genres = data.get('genres', None)
    n = data.get('n', 10)
    
    try:
        recommendations = recommend_for_new_user(genres, n)
        
        return jsonify({
            'status': 'success',
            'type': 'new_user',
            'genres_filter': genres,
            'recommendations': recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/recommend/personalized', methods=['POST'])
def recommend_personalized():
    """Recommandations personnalisées
    
    Body JSON:
    {
        "ratings": {
            "296": 5.0,
            "318": 4.5,
            "260": 4.0
        },
        "n": 10  # Optionnel (défaut: 10)
    }
    """
    data = request.get_json()
    
    ratings_str = data.get('ratings', {})
    n = data.get('n', 10)
    
    # Convertir les clés en int
    ratings = {int(k): float(v) for k, v in ratings_str.items()}
    
    if not ratings:
        return jsonify({
            'status': 'error',
            'message': 'No ratings provided'
        }), 400
    
    try:
        recommendations = recommend_based_on_ratings(ratings, n)
        
        return jsonify({
            'status': 'success',
            'type': 'personalized',
            'num_ratings': len(ratings),
            'recommendations': recommendations.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/search', methods=['GET'])
def search():
    """Rechercher des films par titre
    
    Query params:
    - q: Terme de recherche
    - limit: Nombre de résultats (défaut: 10)
    """
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Query parameter "q" is required'
        }), 400
    
    mask = df_movies['title'].str.contains(query, case=False, na=False)
    results = df_movies[mask][['movieId', 'title', 'genres']].head(limit)
    
    return jsonify({
        'status': 'success',
        'query': query,
        'results': results.to_dict(orient='records')
    })

@app.route('/genres', methods=['GET'])
def get_genres():
    """Obtenir la liste de tous les genres"""
    return jsonify({
        'status': 'success',
        'genres': list(mlb.classes_)
    })

if __name__ == '__main__':
    load_model()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
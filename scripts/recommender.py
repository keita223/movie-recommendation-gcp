"""
Système de recommandation de films
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class MovieRecommender:
    def __init__(self, models_path='../models'):
        """Charger les données et modèles sauvegardés"""
        print("Chargement du modèle...")
        
        self.df_movies = pd.read_pickle(f'{models_path}/df_movies.pkl')
        self.df_ratings = pd.read_pickle(f'{models_path}/df_ratings.pkl')
        self.user_movie_matrix = pd.read_pickle(f'{models_path}/user_movie_matrix.pkl')
        self.genres_df = pd.read_pickle(f'{models_path}/genres_df.pkl')
        
        with open(f'{models_path}/mlb.pkl', 'rb') as f:
            self.mlb = pickle.load(f)
        
        print("✅ Modèle chargé avec succès")
    
    def recommend_for_new_user(self, preferred_genres=None, n_recommendations=10):
        """Recommandations pour nouveaux utilisateurs"""
        movie_popularity = self.df_ratings.groupby('movieId').agg({
            'rating': ['count', 'mean']
        }).reset_index()
        movie_popularity.columns = ['movieId', 'num_ratings', 'avg_rating']
        
        recommendations = self.df_movies.merge(movie_popularity, on='movieId', how='left')
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
        
        return recommendations[['movieId', 'title', 'genres', 'num_ratings', 'avg_rating']].head(n_recommendations)
    
    def recommend_based_on_ratings(self, user_ratings, n_recommendations=10, n_similar_users=20):
        """Recommandations basées sur la similarité"""
        new_user_vector = pd.Series(0, index=self.user_movie_matrix.columns)
        
        for movie_id, rating in user_ratings.items():
            if movie_id in new_user_vector.index:
                new_user_vector[movie_id] = rating
        
        similarities = cosine_similarity(
            [new_user_vector.values],
            self.user_movie_matrix.values
        )[0]
        
        similar_users_idx = np.argsort(similarities)[::-1][:n_similar_users]
        similar_users = self.user_movie_matrix.iloc[similar_users_idx]
        
        weights = similarities[similar_users_idx]
        weighted_ratings = similar_users.T.dot(weights) / weights.sum()
        
        already_rated = list(user_ratings.keys())
        weighted_ratings = weighted_ratings.drop(already_rated, errors='ignore')
        
        top_movies = weighted_ratings.sort_values(ascending=False).head(n_recommendations)
        
        recommendations = self.df_movies[self.df_movies['movieId'].isin(top_movies.index)].copy()
        recommendations['predicted_rating'] = recommendations['movieId'].map(top_movies)
        
        movie_stats = self.df_ratings.groupby('movieId').agg({
            'rating': ['count', 'mean']
        }).reset_index()
        movie_stats.columns = ['movieId', 'num_ratings', 'avg_rating']
        
        recommendations = recommendations.merge(movie_stats, on='movieId', how='left')
        recommendations = recommendations.sort_values('predicted_rating', ascending=False)
        
        return recommendations[['movieId', 'title', 'genres', 'predicted_rating']]
    
    def smart_recommend(self, user_ratings=None, preferred_genres=None, n_recommendations=10):
        """Système hybride intelligent"""
        if user_ratings is None or len(user_ratings) == 0:
            return self.recommend_for_new_user(preferred_genres, n_recommendations)
        elif len(user_ratings) < 5:
            n_collab = n_recommendations // 2
            n_content = n_recommendations - n_collab
            
            collab_recs = self.recommend_based_on_ratings(user_ratings, n_collab)
            content_recs = self.recommend_for_new_user(preferred_genres, n_content)
            
            return pd.concat([collab_recs, content_recs]).head(n_recommendations)
        else:
            return self.recommend_based_on_ratings(user_ratings, n_recommendations)
    
    def get_all_genres(self):
        """Retourne la liste de tous les genres disponibles"""
        return list(self.mlb.classes_)
    
    def search_movies(self, query, limit=10):
        """Recherche de films par titre"""
        mask = self.df_movies['title'].str.contains(query, case=False, na=False)
        results = self.df_movies[mask][['movieId', 'title', 'genres']].head(limit)
        return results
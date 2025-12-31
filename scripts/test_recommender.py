"""
Test du système de recommandation
"""

from recommender import MovieRecommender

# Initialiser le recommender
recommender = MovieRecommender(models_path='../models')

print("\n" + "="*80)
print("TEST 1 : Nouvel utilisateur")
print("="*80)
recs = recommender.smart_recommend(preferred_genres=['Action', 'Sci-Fi'], n_recommendations=5)
print(recs)

print("\n" + "="*80)
print("TEST 2 : Utilisateur avec quelques notes")
print("="*80)
user_ratings = {296: 5.0, 318: 4.5, 260: 4.0}
recs = recommender.smart_recommend(user_ratings=user_ratings, n_recommendations=5)
print(recs)

print("\n" + "="*80)
print("TEST 3 : Liste des genres disponibles")
print("="*80)
print(recommender.get_all_genres())

print("\n✅ Tous les tests réussis !")
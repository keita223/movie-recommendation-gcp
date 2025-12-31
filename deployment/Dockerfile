# Image de base Python
FROM python:3.10-slim

# Répertoire de travail
WORKDIR /app

# Copier les fichiers
COPY requirements.txt .
COPY app.py .
COPY models/ ./models/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Port exposé
EXPOSE 8080

# Variable d'environnement
ENV PORT=8080

# Commande de démarrage avec Gunicorn (production)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app

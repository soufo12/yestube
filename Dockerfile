# Utilise une image Python légère
FROM python:3.10-slim

# Installe ffmpeg proprement
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Définit le dossier de travail
WORKDIR /app

# Copie les fichiers de dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code
COPY . .

# Port par défaut pour Railway
ENV PORT=8080
EXPOSE 8080

# Commande de lancement
CMD ["python", "app.py"]
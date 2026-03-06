from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)

# Configuration du dossier temporaire
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- GESTION DES COOKIES (RAILWAY) ---
# Copie le contenu de ton cookies.txt dans une variable YOUTUBE_COOKIES sur Railway
COOKIES_CONTENT = os.environ.get("YOUTUBE_COOKIES")
COOKIES_FILE = "cookies.txt"

if COOKIES_CONTENT:
    with open(COOKIES_FILE, "w") as f:
        f.write(COOKIES_CONTENT)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality', '1080')
    ext = request.form.get('ext', 'mp4')

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    # LOGIQUE DE FORMAT ROBUSTE : 
    # On cherche la qualité demandée, sinon la meilleure en dessous, sinon n'importe quoi qui marche.
    if ext == 'mp3':
        format_selection = 'bestaudio/best'
    else:
        # Tente de trouver la vidéo <= qualité choisie ET l'audio, sinon prend le meilleur fichier unique disponible
        format_selection = f'bestvideo[height<={quality}]+bestaudio/bestvideo+bestaudio/best'

    ydl_opts = {
        'format': format_selection,
        'outtmpl': output_template,
        'merge_output_format': ext if ext != 'mp3' else None,
        'quiet': True,
        'no_warnings': True,
        # Option cruciale pour ignorer les petites erreurs de métadonnées
        'ignoreerrors': True, 
    }

    # Utilisation des cookies si disponibles
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    # Ajout automatique des post-processeurs selon l'extension
    if ext == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraction des infos et téléchargement
            info = ydl.extract_info(url, download=True)
            
            # Détermination de l'extension réelle finale
            actual_ext = ext if ext == 'mp3' else 'mp4'
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{actual_ext}")

            # Nettoyage du serveur après l'envoi au client
            @after_this_request
            def remove_file(response):
                try:
                    time.sleep(2) 
                    if os.path.exists(final_file):
                        os.remove(final_file)
                except Exception as e:
                    print(f"Erreur suppression : {e}")
                return response

            return send_file(
                final_file, 
                as_attachment=True, 
                download_name=f"{info.get('title', 'video')}.{actual_ext}"
            )
            
    except Exception as e:
        return f"Erreur de téléchargement : {str(e)}"

# --- LANCEMENT SUR PORT 8080 (RAILWAY) ---
if __name__ == '__main__':
    # Railway utilise la variable PORT, sinon 8080 par défaut ici
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
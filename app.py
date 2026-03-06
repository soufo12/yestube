from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time
import glob

app = Flask(__name__)

# On s'assure que le dossier existe au démarrage
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Gestion des cookies (Variable d'environnement Railway)
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
    # Template flexible pour l'extension
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        # On demande le meilleur format compatible
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'merge_output_format': ext if ext != 'mp3' else None,
        'quiet': True,
        'no_warnings': True,
    }

    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    if ext == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # --- DETECTION DYNAMIQUE DU FICHIER ---
            # On cherche n'importe quel fichier qui commence par notre file_id
            search_pattern = os.path.join(DOWNLOAD_DIR, f"{file_id}.*")
            found_files = glob.glob(search_pattern)
            
            if not found_files:
                return "Erreur : Le fichier a été téléchargé mais est introuvable sur le serveur. Vérifiez que FFmpeg est installé."
            
            final_file = found_files[0]

            @after_this_request
            def remove_file(response):
                try:
                    # On attend un peu que le transfert commence
                    time.sleep(10)
                    if os.path.exists(final_file):
                        os.remove(final_file)
                except Exception as e:
                    print(f"Erreur suppression : {e}")
                return response

            return send_file(
                final_file,
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.{ext}"
            )
            
    except Exception as e:
        return f"Erreur de téléchargement : {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
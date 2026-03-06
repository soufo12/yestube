from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time
import glob

app = Flask(__name__)

# Configuration du dossier temporaire avec chemin absolu
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Gestion des Cookies (Variable d'environnement Railway YOUTUBE_COOKIES)
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

    # Configuration yt-dlp : tente le MP4 HD, sinon ce qui est dispo
    ydl_opts = {
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
            
            # Recherche du fichier généré (peu importe l'extension finale après fusion)
            search_pattern = os.path.join(DOWNLOAD_DIR, f"{file_id}.*")
            found_files = glob.glob(search_pattern)
            
            if not found_files:
                return "Erreur : Échec de la création du fichier (Vérifiez FFmpeg)."
            
            final_file = found_files[0]

            @after_this_request
            def remove_file(response):
                try:
                    time.sleep(15) # On laisse 15s pour que le stream commence bien
                    if os.path.exists(final_file):
                        os.remove(final_file)
                except:
                    pass
                return response

            return send_file(
                final_file,
                as_attachment=True,
                download_name=f"{info.get('title', 'video')}.{ext}"
            )
            
    except Exception as e:
        return f"Erreur de téléchargement : {str(e)}"

if __name__ == '__main__':
    # Indispensable pour Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
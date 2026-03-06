from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time
import glob

app = Flask(__name__)

# Dossier local pour Railway
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality', '720') # On reste sur 720p pour maximiser le succès
    ext = request.form.get('ext', 'mp4')

    file_id = str(uuid.uuid4())
    output_template = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"

    # Options ultra-compatibles
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,
    }

    # Utilisation des cookies via variable d'env
    if os.environ.get("YOUTUBE_COOKIES"):
        with open("cookies.txt", "w") as f:
            f.write(os.environ.get("YOUTUBE_COOKIES"))
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # On cherche le fichier par son ID
            files = glob.glob(f"{DOWNLOAD_DIR}/{file_id}.*")
            if not files:
                return "Erreur : Fichier non créé par le serveur."
            
            final_file = files[0]

            @after_this_request
            def remove_file(response):
                try:
                    time.sleep(15)
                    if os.path.exists(final_file):
                        os.remove(final_file)
                except: pass
                return response

            return send_file(final_file, as_attachment=True, download_name=f"video.{ext}")
            
    except Exception as e:
        return f"Erreur : {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
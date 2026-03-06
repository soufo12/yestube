from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Récupération des cookies depuis Railway pour éviter le blocage "Bot"
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

    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if ext != 'mp3' else 'bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': ext if ext != 'mp3' else None,
        'quiet': True,
    }

    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            actual_ext = ext if ext != 'mp3' else 'mp3'
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{actual_ext}")

            @after_this_request
            def remove_file(response):
                try:
                    time.sleep(2) 
                    if os.path.exists(final_file):
                        os.remove(final_file)
                except Exception:
                    pass
                return response

            return send_file(final_file, as_attachment=True, download_name=f"{info['title']}.{actual_ext}")
    except Exception as e:
        return f"Erreur : {str(e)}"

if __name__ == '__main__':
    # Force le port 8080 pour Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
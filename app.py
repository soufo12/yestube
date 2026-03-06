from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality')
    ext = request.form.get('ext')

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if ext != 'mp3' else 'bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': ext if ext != 'mp3' else None,
        'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac'] if ext != 'mp3' else [],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if ext == 'mp3' else [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': ext,
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            actual_ext = ext if ext != 'mp3' else 'mp3'
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{actual_ext}")
            
            # --- LOGIQUE DE SUPPRESSION AUTOMATIQUE ---
            @after_this_request
            def remove_file(response):
                try:
                    # On attend une demi-seconde pour être sûr que le fichier est bien "lâché" par le système
                    time.sleep(0.5) 
                    if os.path.exists(final_file):
                        os.remove(final_file)
                        print(f"Nettoyage : {final_file} supprimé.")
                except Exception as error:
                    print(f"Erreur lors de la suppression : {error}")
                return response
            # ------------------------------------------

            return send_file(final_file, as_attachment=True, download_name=f"{info['title']}.{actual_ext}")
            
    except Exception as e:
        return f"Erreur : {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
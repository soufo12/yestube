from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import time

app = Flask(__name__)

# Dossier temporaire pour les téléchargements
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality') # Ex: 1080, 2160
    ext = request.form.get('ext')         # Ex: mp4, mp3

    # Génération d'un nom unique pour éviter les conflits entre utilisateurs
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    # Configuration optimisée pour la netteté (évite le flou)
    ydl_opts = {
        # On prend le meilleur flux vidéo jusqu'à la qualité choisie + le meilleur audio
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if ext != 'mp3' else 'bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': ext if ext != 'mp3' else None,
        
        # Paramètres pour garantir la propreté du fichier final
        'postprocessor_args': [
            '-c:v', 'copy', # Copie directe du flux vidéo YouTube (zéro perte de qualité)
            '-c:a', 'aac',  # Conversion audio standard pour compatibilité
            '-b:a', '192k'
        ] if ext != 'mp3' else [],
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if ext == 'mp3' else [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': ext,
        }],
        
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraction et téléchargement
            info = ydl.extract_info(url, download=True)
            actual_ext = ext if ext != 'mp3' else 'mp3'
            final_file = os.path.join(DOWNLOAD_DIR, f"{file_id}.{actual_ext}")
            
            # --- NETTOYAGE AUTOMATIQUE ---
            # Cette fonction supprime le fichier du serveur juste APRÈS l'envoi au navigateur
            @after_this_request
            def remove_file(response):
                try:
                    # On laisse une petite seconde pour que l'envoi commence bien
                    time.sleep(1) 
                    if os.path.exists(final_file):
                        os.remove(final_file)
                        print(f"DEBUG: Fichier {final_file} supprimé avec succès.")
                except Exception as error:
                    print(f"Erreur Nettoyage: {error}")
                return response
            # -----------------------------

            # Envoi du fichier au PC de l'utilisateur
            return send_file(
                final_file, 
                as_attachment=True, 
                download_name=f"{info['title']}.{actual_ext}"
            )
            
    except Exception as e:
        return f"Erreur critique : {str(e)}. Assurez-vous que FFmpeg est installé sur le serveur."

# --- CONFIGURATION RAILWAY / PRODUCTION ---
if __name__ == '__main__':
    # Railway utilise la variable d'environnement 'PORT'
    # Si on est en local, il prendra 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' est obligatoire pour que le site soit visible en ligne
    app.run(host='0.0.0.0', port=port)
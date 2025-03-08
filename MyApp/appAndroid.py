from flask import Flask, request, jsonify
from flask_cors import CORS
import os, yt_dlp, ffmpeg, threading
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde la app Android

TEMP_DIR = 'MyApp/temp_audio'
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/download', methods=['POST'])
def download():
    """ Recibe una URL y un formato (mp3/mp4), descarga el archivo y devuelve la ruta. """
    try:
        data = request.get_json()
        url = data.get('url')
        formato = data.get('formato')  # "mp3" o "mp4"

        if not url or not formato:
            return jsonify({"error": "Faltan parámetros (url, formato)."}), 400

        file_path = download_video(url, formato)

        if file_path and os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            file_url = f"http://{request.host}/files/{file_name}"  # URL accesible para Android

            # Programar eliminación en 10 segundos
            threading.Timer(10, lambda: os.remove(file_path) if os.path.exists(file_path) else None).start()

            return jsonify({"message": "Descarga completada", "file": file_url}), 200
        else:
            return jsonify({"error": "No se pudo descargar el archivo."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def download_video(url, formato):
    """ Descarga y convierte videos de YouTube en mp3 o mp4. """
    try:
        ydl_opts = {
            'format': 'bestaudio/best' if formato == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if formato == 'mp3':
            mp3_file = os.path.join(TEMP_DIR, f"{os.path.splitext(os.path.basename(filename))[0]}.mp3")
            ffmpeg.input(filename).output(mp3_file, audio_bitrate='192k').run()
            os.remove(filename)
            return mp3_file
        else:
            return filename

    except Exception as e:
        raise e

@app.route('/files/<filename>')
def serve_file(filename):
    """ Servir los archivos descargados. """
    return app.send_static_file(os.path.join(TEMP_DIR, filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
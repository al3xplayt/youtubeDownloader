"""
Author: Alejandro
Version: 1.0
Date: Febrary 2025
"""

from flask import Flask, render_template, request, redirect, url_for, send_file, flash, after_this_request
import os, yt_dlp, ffmpeg, threading, json
from pathlib import Path
app = Flask(__name__)
app.secret_key = 'your_secret_key'

TEMP_DIR = 'MyApp/temp_audio'
os.makedirs(TEMP_DIR, exist_ok=True)
os.system('pwd')

is_render = os.getenv('RENDER') is not None
cookies = None  # No se establecen cookies en local
if is_render:
    cookiesPath = Path('/etc/secrets/cookies.json')
print("--------------------------------------------------------------------")
print(f"Cookies:\n{cookies}")
print("--------------------------------------------------------------------")
def download_video(url, formato):
    try:
        # Definir opciones para yt-dlp según el formato
        if formato == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'cookiesfile': None,
                'age_limit': 25,
                'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }
            if cookies:
                ydl_opts['cookies'] = cookiesPath
        else:  # Descargar como MP4
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
            }
            if cookies:
                ydl_opts['cookies'] = cookies
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Buscar el archivo descargado
        filename = None
        for file in os.listdir(TEMP_DIR):
            if formato == 'mp3' and file.endswith(('.mp4', '.webm', '.m4a', '.flv')):
                filename = os.path.join(TEMP_DIR, file)
                break
            elif formato == 'mp4' and file.endswith('.mp4'):
                filename = os.path.join(TEMP_DIR, file)
                break

        if not filename:
            raise Exception("No se encontró un archivo descargado.")

        # Si es MP3, convertirlo
        if formato == 'mp3':
            mp3_file = os.path.join(TEMP_DIR, f"{os.path.splitext(os.path.basename(filename))[0]}.mp3")
            ffmpeg.input(filename).output(mp3_file, audio_bitrate='192k').run()
            os.remove(filename)
            return mp3_file
        else:
            return filename  # Retornar el archivo MP4 directamente

    except Exception as e:
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_page', methods=['GET', 'POST'])
def download_page():
    if request.method == 'POST':
        url = request.form['url']
        formato = request.form['formato']  # Capturar formato seleccionado (mp3 o mp4)

        if not url:
            return "No se proporcionó un enlace válido", 400

        try:
            file_path = download_video(url, formato)
            if file_path and os.path.exists(file_path):
                file = Path("temp_audio") / os.path.basename(file_path)
                
                def delete_file():
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Archivo eliminado: {file_path}")
                    except Exception as e:
                        print(f"Error al eliminar archivo: {e}")

                # Ejecutar la eliminación en un hilo después de 5 segundos
                threading.Timer(5, delete_file).start()
                
                return send_file(file, as_attachment=True)
            else:
                return "No se pudo procesar el archivo.", 500
        except Exception as e:
            return str(e), 500

    return render_template('download_page.html')
@app.route('/changeFormats', methods=['POST'])
def changeFormats():
    if request.method == 'POST':
        url = request.form['url']
        formato = request.form['formato']  # Capturar formato seleccionado (mp3 o mp4)
        if not url:
            return "No se proporcionó un enlace válido", 400
        try:
            file_path = download_video(url, formato)
            if file_path and os.path.exists(file_path):
                file = Path("temp_audio") / os.path.basename(file_path)
                def delete_file():
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Archivo eliminado: {file_path}")
                    except Exception as e:
                        print(f"Error al eliminar archivo: {e}")
                # Ejecutar la eliminación en un hilo después de 5 segundos
                threading.Timer(5, delete_file).start()
                return send_file(file, as_attachment=True)
            else:
                return "No se pudo procesar el archivo.", 500
        except Exception as e:
            return str(e), 500
    return render_template('changeFormatFiles.html')
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
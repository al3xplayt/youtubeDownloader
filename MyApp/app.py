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

TEMP_DIR_FILES = 'MyApp/temp_files'
os.makedirs(TEMP_DIR_FILES, exist_ok=True)

is_render = os.getenv('RENDER') is not None
cookies = None  # No se establecen cookies en local
if is_render:
    cookiesPath = Path('/etc/secrets/cookies.json')

def download_video(url, formato):
    try:
        # Definir opciones para yt-dlp según el formato
        if formato == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
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
                threading.Timer(10, delete_file).start()
                
                return send_file(file, as_attachment=True)
            else:
                return "No se pudo procesar el archivo.", 500
        except Exception as e:
            return str(e), 500

    return render_template('download_page.html')

@app.route('/changeFormats', methods=['POST', 'GET'])
def changeFormats():
    if request.method == 'POST':
        # Obtener el archivo cargado y el formato seleccionado
        archivo = request.files['url']
        formato = request.form['formato']  # Capturar formato seleccionado (mp3, wav, mp4, avi, etc.)
        
        if archivo.filename == '':
            return "No se proporcionó un archivo válido", 400
        
        try:
            # Guardar el archivo temporalmente
            archivo_path = os.path.join(TEMP_DIR_FILES, archivo.filename)
            archivo.save(archivo_path)

            # Obtener la extensión del archivo y el nuevo nombre según el formato
            ext = os.path.splitext(archivo.filename)[1]
            if formato == 'mp3':
                output_file = os.path.join(TEMP_DIR_FILES, f"{os.path.splitext(archivo.filename)[0]}.mp3")
                ffmpeg.input(archivo_path).output(output_file).run()
            elif formato == 'wav':
                output_file = os.path.join(TEMP_DIR_FILES, f"{os.path.splitext(archivo.filename)[0]}.wav")
                ffmpeg.input(archivo_path).output(output_file).run()
            elif formato == 'mp4':
                output_file = os.path.join(TEMP_DIR_FILES, f"{os.path.splitext(archivo.filename)[0]}.mp4")
                ffmpeg.input(archivo_path).output(output_file).run()
            elif formato == 'avi':
                output_file = os.path.join(TEMP_DIR_FILES, f"{os.path.splitext(archivo.filename)[0]}.avi")
                ffmpeg.input(archivo_path).output(output_file).run()
            else:
                return "Formato no soportado", 400

            # Verificar si el archivo de salida existe
            if os.path.exists(output_file):
                

                def delete_file():
                    try:
                        if os.path.exists(output_file):
                            os.remove(output_file)
                            print(f"Archivo eliminado: {output_file}")
                    except Exception as e:
                        print(f"Error al eliminar archivo: {e}")
                
                # Ejecutar la eliminación en un hilo después de 5 segundos
                threading.Timer(5, delete_file).start()
                fileName = "temp_files/" + os.path.basename(output_file)
                # Devolver el archivo convertido al usuario
                return send_file(fileName, as_attachment=True)
            else:
                return "No se pudo procesar el archivo.", 500
        except Exception as e:
            return str(e), 500
    
    return render_template('changeFormatFiles.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
import yt_dlp, os
import ffmpeg

TEMP_DIR = 'temp_audio'
os.makedirs(TEMP_DIR, exist_ok=True)

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        filename = None
        for file in os.listdir(TEMP_DIR):
            if file.endswith(('.mp4', '.webm', '.m4a', '.flv', '.mp3')):  # Formatos comunes de audio
                filename = os.path.join(TEMP_DIR, file)
                break
        if filename is None:
            raise Exception("No se encontró un archivo de audio en la descarga.")
        mp3_file = os.path.join(TEMP_DIR, f"{os.path.splitext(os.path.basename(filename))[0]}.mp3")
        ffmpeg.input(filename).output(mp3_file, audio_bitrate='192k').run()
        os.remove(filename)
        return mp3_file
    except Exception as e:
        raise e


if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=9bZkp7q19f0'
    mp3_file = download_video(url)
    if mp3_file:
        print(f"MP3 file saved as: {mp3_file}")
    else:
        print("Failed to download MP3 file.")
import os
import subprocess
import requests
import shutil
from tempfile import NamedTemporaryFile
import yt_dlp
from pathlib import Path
import platform


SYSTEM = platform.system()
BIN_PATH = Path(r"D:\projects\ytdx\bin")
# BIN_PATH = Path(__file__).parent.parent / 'bin'
FFMPEG_PATH = BIN_PATH / ('ffmpeg.exe' if SYSTEM == 'Windows' else 'ffmpeg')
FFPROBE_PATH = BIN_PATH / ('ffprobe.exe' if SYSTEM == 'Windows' else 'ffprobe')
os.environ["PATH"] += os.pathsep + str(BIN_PATH)
os.environ["FFMPEG"] = str(FFMPEG_PATH)
os.environ["FFPROBE"] = str(FFPROBE_PATH)


class HttpDownloader:
    """
    A clean and simple streaming file downloader.
    Emits progress in percentage and status text (speed or bytes).
    """

    def __init__(self, url, filename=None, chunk_size=1024 * 256):
        self.url = url
        self.filename = filename or os.path.basename(url)
        self.chunk_size = chunk_size

    def download(self, progress_callback=None, status_callback=None):
        """
        progress_callback(pct: float)
        status_callback(text: str)
        """
        r = requests.get(self.url, stream=True)
        total = int(r.headers.get("content-length", 0)) or None

        if total:
            scale = 100 / total
        else:
            scale = None

        downloaded = 0

        with NamedTemporaryFile(delete=False) as temp:
            for chunk in r.iter_content(chunk_size=self.chunk_size):
                if not chunk:
                    continue

                temp.write(chunk)
                downloaded += len(chunk)

                # Update progress %
                if scale:
                    pct = downloaded * scale
                    if progress_callback:
                        progress_callback(min(pct, 100.0))

                # Update status text (e.g. "12.4 MB / 48 MB")
                if status_callback and total:
                    mb_dl = downloaded / 1024 / 1024
                    mb_tot = total / 1024 / 1024
                    status_callback(f"{mb_dl:.1f} MB / {mb_tot:.1f} MB")

        shutil.move(temp.name, self.filename)
        return self.filename


class YTDownloader:

    def download(self, url, outdir, fmt='best', process_callback=None):
        os.makedirs(outdir, exist_ok=True)
        opts = {
            'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'progress_hooks': [process_callback] if process_callback else [],
            'ffmpeg_location': str(BIN_PATH / 'ffmpeg.exe'),
            # 'ffprobe_location': str(FFPROBE_PATH),
        }
        subprocess.run([str(FFMPEG_PATH), '-version'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("FFmpeg works!")
        if fmt == 'Audio (mp3)':
            opts.update({'format': 'bestaudio', 'postprocessors': [{
                'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'
            }]})
        elif fmt == 'Audio (m4a)':
            opts.update({'format': 'bestaudio', 'postprocessors': [{
                'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '192'
            }]})
        elif fmt == '720p':
            opts.update({
                'format': 'bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[ext=mp4]'
            })
        elif fmt == '360p':
            opts.update({
                'format': 'bv*[ext=mp4][height<=360]+ba[ext=m4a]/b[ext=mp4]'
            })
        else:
            opts.update({
                'format': "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"
            })

        print(f"Downloading with options: {opts}")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info


def download_missing_binaries():

    binaries = {
        "Linux": {
            "ffmpeg": {"exe": "ffmpeg-linux64-v4.1", 'path': FFMPEG_PATH},
            "ffprobe": {"exe": "ffprobe-linux64-v4.1", 'path': FFPROBE_PATH},

        },
        "Darwin": {
            "ffmpeg": {"exe": "ffmpeg-osx64-v4.1", 'path': FFMPEG_PATH},
            "ffprobe": {"exe": "ffprobe-osx64-v4.1", 'path': FFPROBE_PATH},

        },
        "Windows": {
            "ffmpeg": {"exe": "ffmpeg-win64-v4.1.exe", 'path': FFMPEG_PATH},
            "ffprobe": {"exe": "ffprobe-win64-v4.1.exe", 'path': FFPROBE_PATH},

        },
    }

    bin_dir = Path(BIN_PATH)
    bin_dir.mkdir(exist_ok=True)
    dependancies = ['ffmpeg', 'ffprobe']
    for dep in dependancies:
        file = binaries[SYSTEM][dep]
        url = (
            "https://github.com/imageio/imageio-binaries/raw/183aef992339cc5a463528c75dd298db15fd346f/ffmpeg/"
            + file["exe"]
        )
        if not file['path'].exists():
            httpDownloader = HttpDownloader(url=url, filename=str(file['path']))
            httpDownloader.download()

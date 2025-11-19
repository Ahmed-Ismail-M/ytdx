import os
import requests
import shutil
from tempfile import NamedTemporaryFile
import yt_dlp

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
        }


        if fmt == 'Audio (mp3)':
            opts.update({'format': 'bestaudio', 'postprocessors': [{
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'
            }]})
        elif fmt == 'Audio (m4a)':
            opts.update({'format': 'bestaudio', 'postprocessors': [{
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '192'
            }]})
        elif fmt == '720p':
            opts.update({'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]'})
        elif fmt == '360p':
            opts.update({'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]'})
        else:
            opts.update({'format': 'best'})

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info
        
    

    
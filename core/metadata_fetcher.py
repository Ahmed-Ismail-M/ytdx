from concurrent.futures import ThreadPoolExecutor
import yt_dlp
import requests

class MetadataFetcher:
    """
    Extracts title + thumbnail async, using yt_dlp if available.
    """
    _executor = ThreadPoolExecutor(max_workers=4)

    @staticmethod
    def fetch_async(url, callback):
        """
        callback(title: str | None, thumbnail_pixmap: QPixmap | None)
        """

        def task():
            title = None
            thumb_url = None

            # Try using Python yt_dlp
            try:
                opts = {"quiet": True, "skip_download": True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title")
                    thumb_url = info.get("thumbnail")
            except Exception:
                pass

            # Download thumbnail
            content = None
            if thumb_url:
                try:
                    r = requests.get(thumb_url, timeout=8)
                    if r.status_code == 200:
                        content = r.content
                        # pix = QPixmap()
                        # pix.loadFromData(r.content)
                except Exception:
                    pass

            return title, content

        future = MetadataFetcher._executor.submit(task)

        def done(fut):
            try:
                title, pix = fut.result()
                callback(title, pix)
            except Exception:
                callback(None, None)

        future.add_done_callback(done)

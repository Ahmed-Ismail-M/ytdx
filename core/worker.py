import os
from PySide6.QtCore import QRunnable
from core.downloader import HttpDownloader
from core.downloader import YTDownloader
from core.signals import DownloadWorkerSignals
from core.types import DownloadTypes


class DownloadTask(QRunnable):
    def __init__(self, url, outdir, fmt, signals: DownloadWorkerSignals, downloadTypes: DownloadTypes):
        super().__init__()
        self.url = url
        self.outdir = outdir
        self.fmt = fmt
        self.downloadTypes = downloadTypes
        self.signals = signals

    def run(self):
        try:
            if self.downloadTypes == DownloadTypes.YTDLP:
                self.download_yt()
            if self.downloadTypes == DownloadTypes.HTTP:
                self.download_file()
        except Exception as e:
            self.signals.status.emit(f'Error: {e}')
            self.signals.finished.emit(False, str(e))

    def download_file(self):
        filename = os.path.join(self.outdir, os.path.basename(self.url))
        d = HttpDownloader(self.url, filename=filename)
        self.signals.status.emit('Starting HTTP download')
        d.download(progress_callback=lambda p: self.signals.progress.emit(p),
                   status_callback=lambda s: self.signals.status.emit(s))
        self.signals.finished.emit(True, filename)

    def download_yt(self):
        ytd = YTDownloader()
        self.signals.status.emit('Starting yt-dlp')
        info = ytd.download(self.url, self.outdir, self.fmt, process_callback=self._progress_hook)
        self.signals.status.emit('Done')
        self.signals.finished.emit(True, info.get('title', ''))

    def _progress_hook(self, d):
        # d is dict with status info
        if d.get('status') == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            try:
                pct = (downloaded / total_bytes) * 100 if total_bytes else 0.0
            except Exception:
                pct = 0.0
            self.signals.progress.emit(min(max(pct, 0.0), 100.0))
            self.signals.status.emit(d.get('eta') and f"ETA: {d.get('eta')}")
        elif d.get('status') == 'finished':
            self.signals.progress.emit(100.0)
            self.signals.status.emit('Merging / finalizing...')

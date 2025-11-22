from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QApplication, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from core.signals import DownloadWorkerSignals
from core.types import DownloadTypes
from core.worker import DownloadTask

class LinkItemWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.worker = None

        # Layouts
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(self.layout)

        # Thumbnail
        self.thumb = QLabel()
        self.thumb.setFixedSize(96, 54)
        self.thumb.setScaledContents(True)
        self.thumb.setPixmap(self.style().standardPixmap(QStyle.SP_FileIcon).scaled(96, 54))

        # Info layout
        self.info_layout = QVBoxLayout()
        self.title_label = QLabel(url)
        self.title_label.setWordWrap(True)
        self.status_label = QLabel('Waiting')
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFixedHeight(14)
        self.info_layout.addWidget(self.title_label)
        self.info_layout.addWidget(self.status_label)
        self.info_layout.addWidget(self.progress)

        # Buttons
        self.download_button = QPushButton("Download")
        self.download_button.setFixedSize(60, 24)
        self.download_button.clicked.connect(self.download)

        # Assemble layout
        self.layout.addWidget(self.thumb)
        self.layout.addLayout(self.info_layout)
        self.layout.addWidget(self.download_button)

    def download(self):
        main_window = self.window()
        self.set_status("Starting download...")
        signals = DownloadWorkerSignals()
        signals.progress.connect(self.set_progress)
        signals.status.connect(self.set_status)
        signals.finished.connect(self.on_finished)
        self.worker = DownloadTask(
            self.url,
            main_window.download_folder,
            main_window.format_combo.currentText(),
            signals,
            DownloadTypes.YTDLP
        )
        main_window.threadpool.start(self.worker)

    def set_thumbnail(self, qpixmap: QPixmap):
        self.thumb.setPixmap(qpixmap.scaled(96, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_title(self, text):
        self.title_label.setText(text)

    def set_status(self, text):
        self.status_label.setText(str(text))

    def set_progress(self, pct):
        self.progress.setValue(int(pct))

    def stop_download(self):
        if self.worker:
            self.worker.stop()
            self.set_status("Stopping...")
            self.stop_button.setEnabled(False)

    def on_finished(self, success: bool, message: str):
        if success:
            self.set_status('Completed')
            self.set_progress(100)
            QApplication.beep()
        else:
            self.set_status(f'Failed: {message}')

    

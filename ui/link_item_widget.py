from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QStyle
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class LinkItemWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.setLayout(self.layout)

        self.thumb = QLabel()
        self.thumb.setFixedSize(96, 54)
        self.thumb.setScaledContents(True)
        self.thumb.setPixmap(self.style().standardPixmap(QStyle.SP_FileIcon).scaled(96, 54))

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

        self.layout.addWidget(self.thumb)
        self.layout.addLayout(self.info_layout)

    def set_thumbnail(self, qpixmap: QPixmap):
        self.thumb.setPixmap(qpixmap.scaled(96, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_title(self, text):
        self.title_label.setText(text)

    def set_status(self, text):
        self.status_label.setText(str(text))

    def set_progress(self, pct):
        self.progress.setValue(int(pct))


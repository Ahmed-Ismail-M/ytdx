from pathlib import Path
from functools import partial
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QLabel, QComboBox, QCheckBox
)
from PySide6.QtCore import QThreadPool
from PySide6.QtMultimedia import QSoundEffect

from core.config_manager import load_config, save_config
from core.metadata_fetcher import MetadataFetcher
from core.types import DownloadTypes
from core.worker import DownloadTask
from ui.link_item_widget import LinkItemWidget
from core.signals import DownloadWorkerSignals
import qdarktheme
from core.downloader import download_missing_binaries


class DownoaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        qdarktheme.setup_theme()
        self.setWindowTitle('YT Downloader')
        self.setMinimumSize(640, 480)

        self.cfg = load_config()
        download_missing_binaries()

        self.threadpool = QThreadPool.globalInstance()

        main = QVBoxLayout()
        self.setLayout(main)

        # Top row: input + add
        top = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Paste YouTube (or other) link here...')
        self.url_input.setMinimumHeight(36)
        add_btn = QPushButton('Add')
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self.on_add_clicked)
        top.addWidget(self.url_input)
        top.addWidget(add_btn)

        # Middle: list
        self.link_list = QListWidget()
        self.link_list.setAcceptDrops(False)

        # Right-side small toolbar
        toolbar = QHBoxLayout()
        remove_btn = QPushButton('Remove Selected')
        remove_btn.clicked.connect(self.remove_selected)
        download_btn = QPushButton('Download All')
        download_btn.setStyleSheet('background-color: #4CAF50; color: white; font-weight: bold;')
        download_btn.clicked.connect(self.download_all)

        # Format options
        self.format_combo = QComboBox()
        self.format_combo.addItems(
            ['Best (video+audio)', '720p', '360p', 'Audio (mp3)', 'Audio (m4a)'])
        self.format_combo.setCurrentText(self.cfg.get('format_preset', 'Best (video+audio)'))
        self.format_combo.currentTextChanged.connect(
            lambda text: self.cfg.__setitem__('format_preset', text) or save_config(self.cfg))

        # Folder picker
        folder_btn = QPushButton('Choose Folder')
        folder_btn.clicked.connect(self.choose_folder)
        self.folder_label = QLabel(self.cfg.get('last_folder', str(Path.home())))
        self.folder_label.setMinimumWidth(220)

        # Dark mode toggle
        self.dark_toggle = QCheckBox('Dark mode')
        self.dark_toggle.setChecked(self.cfg.get('dark_mode', False))
        self.dark_toggle.stateChanged.connect(self.toggle_dark)
        # sound effect
        self.sound = QSoundEffect()
        toolbar.addWidget(self.format_combo)
        toolbar.addWidget(folder_btn)
        toolbar.addWidget(self.folder_label)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(download_btn)
        toolbar.addWidget(self.dark_toggle)

        main.addLayout(top)
        main.addWidget(self.link_list)
        main.addLayout(toolbar)
        self.setAcceptDrops(True)
        self.download_folder = self.cfg.get('last_folder', str(Path.home()))
        if self.cfg.get('dark_mode'):
            self.apply_dark_style()

    def on_add_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, 'Empty', 'Please enter a valid link')
            return
        self.add_link_item(url)
        self.url_input.clear()

    def add_link_item(self, url):
        item = QListWidgetItem()
        widget = LinkItemWidget(url)
        item.setSizeHint(widget.sizeHint())
        self.link_list.addItem(item)
        self.link_list.setItemWidget(item, widget)
        MetadataFetcher.fetch_async(
            url, lambda title, content: self.update_widget(widget, title, content))

    def update_widget(self, widget, title, content):
        if title:
            widget.set_title(title)
        if content:
            pix = QPixmap()
            pix.loadFromData(content)
            widget.set_thumbnail(pix)

    def remove_selected(self):
        for itm in self.link_list.selectedItems():
            row = self.link_list.row(itm)
            self.link_list.takeItem(row)

    def download_all(self):
        count = self.link_list.count()
        if count == 0:
            QMessageBox.information(self, 'No Links', 'Add links before downloading.')
            return
        fmt = self.format_combo.currentText()
        # iterate items
        for i in range(self.link_list.count()):
            item = self.link_list.item(i)
            widget = self.link_list.itemWidget(item)
            widget.set_status('Queued')
            signals = DownloadWorkerSignals()
            signals.progress.connect(widget.set_progress)
            signals.status.connect(widget.set_status)
            signals.finished.connect(partial(self.on_finished, widget))
            worker = DownloadTask(widget.url, self.download_folder,
                                  fmt, signals, DownloadTypes.YTDLP)
            self.threadpool.start(worker)

    def on_finished(self, widget: LinkItemWidget, success: bool, message: str):
        if success:
            widget.set_status('Completed')
            widget.set_progress(100)
            # beep
            try:
                # try QSoundEffect - if not loaded, fallback to beep
                if self.sound.source().isEmpty():
                    QApplication.beep()
                else:
                    self.sound.play()
            except Exception:
                QApplication.beep()
        else:
            widget.set_status(f'Failed: {message}')

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 'Choose download folder', self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_label.setText(folder)
            self.cfg['last_folder'] = folder
            save_config(self.cfg)

    def toggle_dark(self, state):
        enabled = bool(state)
        self.cfg['dark_mode'] = enabled
        if enabled:
            self.apply_dark_style()
        else:
            self.apply_light_style()
        save_config(self.cfg)

    def apply_dark_style(self):
        qdarktheme.setup_theme("dark")

    def apply_light_style(self):
        qdarktheme.setup_theme("light")

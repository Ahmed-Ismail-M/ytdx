from pathlib import Path
from functools import partial
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QLabel, QComboBox, QCheckBox
)
from PySide6.QtCore import QThreadPool

# Optional: for sound
from PySide6.QtMultimedia import QSoundEffect

from core.config_manager import load_config, save_config
from core.metadata_fetcher import MetadataFetcher
from core.types import DownloadTypes
from core.worker import DownloadTask
from ui.link_item_widget import LinkItemWidget
from core.signals import DownloadWorkerSignals

try:
    import requests
except Exception:
    requests = None


class DownoaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Super Easy YT Downloader')
        self.setMinimumSize(640, 480)

        self.cfg = load_config()

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
        # Use a short system beep via QSoundEffect if available - many systems won't have a file.
        # We'll fallback to QApplication.beep() if playback fails.

        toolbar.addWidget(self.format_combo)
        toolbar.addWidget(folder_btn)
        toolbar.addWidget(self.folder_label)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(download_btn)
        toolbar.addWidget(self.dark_toggle)

        main.addLayout(top)
        main.addWidget(self.link_list)
        main.addLayout(toolbar)
        # main.addWidget(drag_label)

        # Accept drops on the main window
        self.setAcceptDrops(True)

        # set saved folder
        self.download_folder = self.cfg.get('last_folder', str(Path.home()))

        # Apply dark mode if set
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

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 'Choose download folder', self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_label.setText(folder)
            self.cfg['last_folder'] = folder
            save_config(self.cfg)

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

    def toggle_dark(self, state):
        enabled = bool(state)
        self.cfg['dark_mode'] = enabled
        if enabled:
            self.apply_dark_style()
        else:
            self.apply_light_style()
        save_config(self.cfg)

    def apply_dark_style(self):
        self.setStyleSheet('''
            QWidget { background: #2b2b2b; color: #e6e6e6; }
            QLineEdit, QListWidget, QComboBox { background: #3c3c3c; color: #e6e6e6; }
            QPushButton { background: #4CAF50; color: white; border-radius: 6px; padding: 6px; }
        ''')

    def apply_light_style(self):
        self.setStyleSheet('')

    # def dragEnterEvent(self, event: QDragEnterEvent):
    #     if event.mimeData().hasText():
    #         event.acceptProposedAction()

    # def dropEvent(self, event: QDropEvent):
    #     text = event.mimeData().text().strip()
    #     # can contain multiple lines
    #     for line in text.splitlines():
    #         if line.strip():
    #             self.add_link_item(line.strip())

    # def fetch_metadata_async(self, url, widget: LinkItemWidget):
    #     # We'll try to use yt_dlp to extract info without downloading
    #     def task():
    #         title = None
    #         thumb_url = None
    #         try:
    #             if YTDLP_AVAILABLE:
    #                 ydl_opts = {'quiet': True, 'skip_download': True}
    #                 with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #                     info = ydl.extract_info(url, download=False)
    #                     title = info.get('title')
    #                     thumb_url = info.get('thumbnail')
    #             else:
    #                 # use "yt-dlp -j" to get json
    #                 proc = shutil.which('yt-dlp')
    #                 if proc:
    #                     p = subprocess.run(['yt-dlp', '-j', url], capture_output=True, text=True)
    #                     if p.returncode == 0:
    #                         try:
    #                             j = json.loads(p.stdout.splitlines()[0])
    #                             title = j.get('title')
    #                             thumb_url = j.get('thumbnail')
    #                         except Exception:
    #                             pass
    #         except Exception:
    #             pass

    #         # fetch thumbnail image
    #         if thumb_url and requests:
    #             try:
    #                 r = requests.get(thumb_url, timeout=8)
    #                 if r.status_code == 200:
    #                     data = r.content
    #                     pix = QPixmap()
    #                     pix.loadFromData(data)
    #                     return (title, pix)
    #             except Exception:
    #                 pass
    #         return (title, None)

    #     # run in threadpool and update UI when done
    #     from concurrent.futures import ThreadPoolExecutor
    #     executor = ThreadPoolExecutor(max_workers=1)
    #     future = executor.submit(task)

    #     def done(fut):
    #         try:
    #             title, pix = fut.result()
    #             if title:
    #                 widget.set_title(title)
    #             if pix:
    #                 widget.set_thumbnail(pix)
    #         except Exception:
    #             pass

    #     future.add_done_callback(done)

from PySide6.QtCore import QObject, Signal


class DownloadWorkerSignals(QObject):
    progress = Signal(float)  # percent 0..100
    status = Signal(str)
    finished = Signal(bool, str)  # success, message

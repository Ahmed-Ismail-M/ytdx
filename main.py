from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFontDatabase, QFont
from ui.main_window import DownloaderWidget
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("assets/fonts/Inter-VariableFont_opsz,wght.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/Inter-VariableFont_opsz,wghtttf")
    # QFontDatabase.addApplicationFont("assets/fonts/Inter-Bold.ttf")
    app.setFont(QFont("Inter", 11))
    app.setWindowIcon(QIcon("assets/media/downloading.png"))
    window = DownloaderWidget()
    window.show()
    sys.exit(app.exec())

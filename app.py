from PySide6.QtWidgets import QApplication
from ui.main_window import DownoaderWidget
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownoaderWidget()
    window.show()
    sys.exit(app.exec())

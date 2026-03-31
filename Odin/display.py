import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt


class SmileyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azul")
        self.setFixedSize(300, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Face
        painter.setBrush(QColor(255, 220, 50))
        painter.setPen(QPen(Qt.black, 3))
        painter.drawEllipse(50, 50, 200, 200)

        # Left eye
        painter.setBrush(Qt.black)
        painter.drawEllipse(105, 110, 20, 20)

        # Right eye
        painter.drawEllipse(175, 110, 20, 20)

        # Smile
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(Qt.black, 4))
        painter.drawArc(95, 130, 110, 80, 0, -180 * 16)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmileyWindow()
    window.show()
    sys.exit(app.exec_())

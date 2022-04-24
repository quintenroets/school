import os

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

# disable annoying warnings
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

MARGIN = 10
TEXT_HEIGHT = 174
HEIGHT = 250
WIDTH = 370
PROGRESS_HEIGHT = 14


class WidgetUI(QtWidgets.QDialog):
    def __init__(self, message=""):
        super().__init__()
        self.initUI(message)
        self.onCancel = None
        self.onOpen = None
        self.onClose = None

    def initUI(self, message):
        scroll = QtWidgets.QScrollArea(self)
        scroll.move(MARGIN, MARGIN)
        scroll.setFixedWidth(WIDTH - 2 * MARGIN)
        scroll.setFixedHeight(TEXT_HEIGHT)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)

        vbox = QtWidgets.QVBoxLayout(scroll)
        for m in message.split("\n"):
            vbox.addWidget(QtWidgets.QLabel(m))

        scrollwidget = QtWidgets.QWidget(self)
        scrollwidget.setLayout(vbox)
        scroll.setWidget(scrollwidget)

        progress = QtWidgets.QProgressBar(self)
        progress.move(MARGIN, TEXT_HEIGHT + 2 * MARGIN)
        progress.setFixedWidth(WIDTH - 2 * MARGIN)
        progress.setFixedHeight(PROGRESS_HEIGHT)

        cancel = QtWidgets.QPushButton("Cancel", self)
        cancel.move(MARGIN, TEXT_HEIGHT + 3 * MARGIN + PROGRESS_HEIGHT)

        open = QtWidgets.QPushButton("Open after download", self)
        open.move(MARGIN + 100, TEXT_HEIGHT + 3 * MARGIN + PROGRESS_HEIGHT)

        close = QtWidgets.QPushButton("OK", self)
        close.move(MARGIN + 250, TEXT_HEIGHT + 3 * MARGIN + PROGRESS_HEIGHT)

        self.setWindowTitle("School")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.focusWidget()

        self.setGeometry(1500, 580, WIDTH, HEIGHT)
        self.show()

        self.scroll = scroll
        self.vbox = vbox
        self.scrollwidget = scrollwidget
        self.progress = progress

        self.cancel = cancel
        self.open = open
        self.closeButton = close

from .widgetui import WidgetUI


class Widget(WidgetUI):
    def __init__(self, message=""):
        super().__init__(message=message)
        self.onCancel = None
        self.onOpen = None
        self.onClose = None
        self.enable_keyclose = False

        self.closeButton.setDisabled(True)
        self.closeButton.clicked.connect(self.close_clicked)
        self.open.clicked.connect(self.open_clicked)
        self.cancel.clicked.connect(self.cancel_clicked)

    def keyPressEvent(self, event):
        if event.key() == 16777220:  # Enter key
            if self.enable_keyclose:
                self.close()

    def close_clicked(self):
        if self.onClose:
            self.onClose()

    def open_clicked(self):
        if self.onOpen:
            self.onOpen()

    def cancel_clicked(self):
        if self.onCancel:
            self.onCancel()

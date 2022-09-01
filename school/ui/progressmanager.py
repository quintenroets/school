import threading
import time

from .popup import SilentUIHandle
from .progressbar import ProgressBar


class Progress(ProgressBar):
    def __init__(self, message="Checking for new items", silent=False):
        super().__init__(title="School", message=message, silent=silent)
        self.messages = [message]
        self.auto_max = 0.0
        self.auto_add_value = 0.001

        self.do_auto_add = True
        self.auto_progress = 0

    def __enter__(self):
        super().__enter__()
        self.auto_add()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.do_auto_add = False
        super().__exit__(exc_type, exc_val, exc_tb)

    def add_message(self, message):
        self.messages.append(self.message)
        self.message = message

    def pop_message(self):
        if len(self.messages) > 0:
            message = self.messages.pop()
            self.message = message

    def auto_add(self):
        threading.Thread(target=self._auto_add).start()

    def _auto_add(self):
        while self.do_auto_add:
            if self.auto_progress < self.auto_max:
                self.auto_progress += self.auto_add_value
            time.sleep(0.005)

    def add_progress(self, value):
        self.progress += value

    @property
    def percentage(self):
        return max(super().percentage, self.auto_progress * 100)

    def reset(self):
        self.progress = 0


class ProgressManager:
    progress = Progress(silent=True)

    @classmethod
    def __enter__(cls):
        ProgressManager.progress = Progress()
        ProgressManager.progress.__enter__()

    @classmethod
    def __exit__(cls, exc_type, exc_val, exc_tb):
        ProgressManager.progress.__exit__(exc_type, exc_val, exc_tb)

    @classmethod
    @property
    def interactive_mode(cls):
        return not isinstance(cls.progress.handle, SilentUIHandle)

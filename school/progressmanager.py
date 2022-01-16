import time
import threading

from libs.progressbar import ProgressBar


class Progress(ProgressBar):
    def __init__(self, message='Checking for new items'):
        super(Progress, self).__init__(title='School', message=message, show_progress_message=False)
        self.messages = [message]
        self.auto_max = 0.0
        self.auto_add_value = 0.001

        self.do_auto_add = True
        self.auto_progress = 0


    def __enter__(self):
        super(Progress, self).__enter__()
        self.auto_add()

    def add_message(self, message):
        self.messages.append(message)
        self.set_message(message)

    def pop_message(self):
        if len(self.messages) > 1:
            self.messages.pop()
        self.set_message(self.messages[-1])

    def auto_add(self):
        threading.Thread(target=self._auto_add).start()

    def _auto_add(self):
        while self.do_auto_add:
            self.set_progress(self.progress_value)
            if self.auto_progress < self.auto_max:
                self.auto_progress += self.auto_add_value
            time.sleep(0.005)

    def show_progress(self, percentage=None):
        if not percentage:
            normal_progress = self.progress_value / self.amount if self.amount else 0
            percentage = 100 * max(normal_progress, self.auto_progress)

        super(Progress, self).show_progress(percentage)

    def reset(self):
        self.progress_value = 0


class ProgressManager:
    progress = None

    @staticmethod
    def __enter__():
        ProgressManager.progress = Progress()
        ProgressManager.progress.__enter__()

    @staticmethod
    def __exit__(exc_type, exc_val, exc_tb):
        ProgressManager.progress.do_auto_add = False
        ProgressManager.progress.__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def add(coursemanager):
        ProgressManager.progress.amount += len(coursemanager.old_content) + 10000 # extra constant delay

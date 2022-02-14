import sys
import threading

from PyQt6 import QtWidgets

cond = threading.Condition()


class UserInterface:
    tasks = []
    to_show = 0
    checked = 0

    @staticmethod
    def show_progres(to_check):
        done = 0
        app = None

        while done < UserInterface.to_show or UserInterface.checked < to_check:
            if not UserInterface.tasks or UserInterface.checked < to_check:
                with cond:
                    cond.wait()
            if UserInterface.tasks:
                if app is None:
                    app = QtWidgets.QApplication(sys.argv)
                downloadprogress = UserInterface.tasks.pop(0)
                downloadprogress.grant_widget()
                done += 1
                with cond:  # allow new tasks
                    cond.notifyAll()

    @staticmethod
    def add_check(amount):
        UserInterface.checked += 1
        UserInterface.to_show += amount
        with cond:
            cond.notifyAll()

    @staticmethod
    def request_widget(downloadprogress):
        if downloadprogress not in UserInterface.tasks:
            with cond:
                UserInterface.tasks.append(downloadprogress)
                cond.notifyAll()

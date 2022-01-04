from libs.opener import startfile

from .widget import Widget


class DownloadProgress:
    def __init__(self, section):
        self.finished = False
        self.to_show = False
        self.section = section
        self.amount = 0
        self.progres_value = 0

        self.widget = None

    def request_widget(self):
        from .userinterface import UserInterface
        UserInterface.request_widget(self)

    def grant_widget(self):
        self.widget = Widget(self.make_message(self.section))

        self.widget.onCancel = self.onCancel
        self.widget.onOpen = self.onOpen
        self.widget.onClose = self.onClose
        progress = 1 if self.finished else None
        self.set_progress(progress)

        self.widget.exec()

    def onCancel(self):
        self.widget.close()
        self.widget = None
        raise KeyboardInterrupt

    def onOpen(self):
        if self.finished:
            self.show_download()
        else:
            self.to_show = True

    def onClose(self):
        self.widget.close()
        self.widget = None

    def set_progress(self, progress=None):
        if self.widget is None:
            self.request_widget()

        if self.amount and not progress:
            progress = self.progres_value / self.amount
        if progress and self.widget:
            self.widget.progress.setValue(progress * 100)
            if progress == 1:
                self.widget.closeButton.setDisabled(False)
                self.widget.enable_keyclose = True

    def add_progress(self, progress):
        self.progres_value += progress
        self.set_progress()

    def add_amount(self, amount):
        self.amount += amount
        self.set_progress()

    def make_message(self, section):
        arrow = u"\u2B9E "
        title = [section.coursemanager.course.name] + [i * "   " + arrow + part for i, part in enumerate(section.titles)]
        content = [s.title + " (updated)" if s.updated else s.title for s in section.items]
        message = "\n".join(title + [""]  + content)
        return message

    def show_download(self):
        self.onClose()

        files = [self.section.dest]
        if not self.section.announ:
            files += [it.dest for it in self.section.items if it.dest and not it.dest.suffix == ".ipynb"]
        if any([f.suffix == ".mp4" for f in files]):
            files = [f for f in files if not f.suffix == ".mp4"] + [self.section.dest / "Videos.html"]

        for f in files:
            startfile(f)

    def enable_show(self):
        self.set_progress(1)
        if self.to_show:
            self.show_download()
        else:
            self.finished = True

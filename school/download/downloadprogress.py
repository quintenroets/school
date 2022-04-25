from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import cli

from school.ui.widget import Widget

if TYPE_CHECKING:
    from school.content.contentmanager import SectionInfo


@dataclass
class DownloadProgress:
    section: SectionInfo
    finished: bool = False
    to_show: bool = False
    amount: int = 0
    progress_value: int = 0
    widget: Any = None

    def request_widget(self):
        from school.ui.userinterface import UserInterface  # noqa: autoimport

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
            progress = self.progress_value / self.amount
        if progress and self.widget:
            value = int(progress * 100)
            self.widget.progress.setValue(value)
            if progress == 1:
                self.widget.closeButton.setDisabled(False)
                self.widget.enable_keyclose = True

    def add_progress(self, progress):
        self.progress_value += progress
        self.set_progress()

    def add_amount(self, amount):
        self.amount += amount
        self.set_progress()

    def make_message(self, section):
        arrow = "\u2B9E "
        title = [section.coursemanager.course.name] + [
            i * "   " + arrow + part for i, part in enumerate(section.titles)
        ]
        content = [
            it.title if not it.toc_info or not it.updated else it.title + " (updated)"
            for it in section.items
        ]
        message = "\n".join(title + [""] + content)
        return message

    def show_download(self):
        self.onClose()

        urls = [self.section.dest]
        if not self.section.announ:
            dests = [it.dest for it in self.section.items]
            if any([d.suffix == ".mp4" for d in dests]):
                urls.append(self.section.dest / "Videos.html")
            urls += [d for d in dests if d.suffix != ".mp4"]
        cli.urlopen(*urls)

    def enable_show(self):
        self.set_progress(1)
        if self.to_show:
            self.show_download()
        else:
            self.finished = True

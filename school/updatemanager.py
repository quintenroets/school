from libs.threading import Threads

from . import constants
from .downloader import Downloader
from .downloadmanager import DownloadManager
from .path import Path
from .userinterface import UserInterface


class UpdateManager:
    @staticmethod
    def process_updates(contentmanager):
        contentmanager.new_topic_sections = [
            s for s in contentmanager.sections if s.changed and not s.only_subfolders
        ]
        downloaders = [
            Downloader(s).download_section for s in contentmanager.new_topic_sections
        ]

        UserInterface.add_check(len(downloaders))
        downloaders = Threads(downloaders).start()

        for section in contentmanager.sections:
            if section.changed and section.only_subfolders:
                DownloadManager.make_section(section)
            if not section.changed and section.order_changed:
                DownloadManager.update_order(section)

        downloaders.join()

        if constants.update_content:
            c = contentmanager
            Path.content(c.coursemanager.course.name, c.coursemanager.part).write(
                c.content_bytes
            )

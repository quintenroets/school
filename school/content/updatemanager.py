from libs.threading import Threads
from school.download.downloader import Downloader
from school.download.downloadmanager import DownloadManager
from school.ui.userinterface import UserInterface
from school.utils import constants
from school.utils.path import Path


class UpdateManager:
    @staticmethod
    def process_updates(contentmanager):
        contentmanager.new_topic_sections = [
            s for s in contentmanager.sections if s.changed
        ]
        downloaders = [
            Downloader(s).download_section for s in contentmanager.new_topic_sections
        ]

        UserInterface.add_check(len(downloaders))
        downloaders = Threads(downloaders).start()

        for section in contentmanager.sections:
            DownloadManager.make_section(section)

        downloaders.join()

        if constants.update_content:
            c = contentmanager
            Path.content_path(
                c.coursemanager.course.name, c.coursemanager.part
            ).byte_content = c.content_bytes

from school.clients.session import D2LApi
from school.clients.zoomapi import ZoomApi
from school.ui.progressmanager import ProgressManager
from school.ui.userinterface import UserInterface
from school.utils.path import Path


class CourseManager:
    def __init__(self, course, part):
        self.course = course
        self.api = D2LApi(course)
        self.part = part
        self.contentmanager = None
        self.old_content = Path.content_path(self.course.name, self.part).read_bytes()
        ProgressManager.progress.amount += 1

    def check(self):
        content = (
            ZoomApi.get_content(self.course.id)
            if self.part == "zoom"
            else self.api.get(self.part)
        )
        ProgressManager.progress.progress += 1

        if content != self.old_content:
            self.process_changes(content, self.old_content)
        else:
            UserInterface.add_check(0)

    def process_changes(self, content, old_content):
        from .contentmanager import ContentManager
        from .updatemanager import UpdateManager

        self.contentmanager = ContentManager(content, old_content, self.part, self)
        UpdateManager.process_updates(self.contentmanager)

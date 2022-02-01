import json
from datetime import datetime

from .path import Path
from .progressmanager import ProgressManager
from .session import D2LApi, session
from .userinterface import UserInterface
from .zoomapi import ZoomApi


class CourseManager:
    def __init__(self, course, part):
        self.course = course
        self.api = D2LApi(course)
        self.part = part
        self.contentmanager = None
        self.old_content = Path.content_path(self.course.name, self.part).read_bytes()
        ProgressManager.add(self)

    def check(self):
        if self.part == "zoom":
            content = ZoomApi.get_content(self.course.id)
            ProgressManager.progress.add_progress(
                len(self.old_content) + 1000
            )  # set as progress when request done
        else:
            content = self.api.get(self.part)
            ProgressManager.progress.add_progress(1000)
            # Here progress is accumulated during request

        if content != self.old_content:
            self.process_changes(content, self.old_content)
        else:
            UserInterface.add_check(0)

    @staticmethod
    def check_notifications():
        last_announ_seen = Path.content_path(
            "notifications", "notifications"
        ).read_text()

        if not last_announ_seen:
            last_announ_seen = CourseManager.to_string(
                datetime.now().replace(year=last_announ_seen.year - 1)
            )

        new_announ_url = (
            "https://ufora.ugent.be/d2l/api/lp/1.30/feed/?since={last_announ_seen}"
        )

        content = session.get(new_announ_url).content
        changed = content != b"[]"

        if changed:
            Path.content_path(
                "notifications", "notifications"
            ).text = CourseManager.to_string(datetime.now())
            last_announ = json.loads(content)[0]["Metadata"]["Date"]
            changed = last_announ_seen < last_announ

        return changed

    @staticmethod
    def to_string(time):
        return str(time).replace(" ", "T")[:-3] + "Z"

    def process_changes(self, content, old_content):
        from .contentmanager import ContentManager
        from .updatemanager import UpdateManager

        self.contentmanager = ContentManager(content, old_content, self.part, self)
        UpdateManager.process_updates(self.contentmanager)

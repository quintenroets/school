import json
from datetime import datetime

from .progressmanager import ProgressManager
from .sessionmanager import D2LApi, SessionManager
from .userinterface import UserInterface
from .bongoapi import BongoApi
from .zoomapi import ZoomApi

from .path import Path


class CourseManager:
    def __init__(self, course, part):
        self.course = course
        self.api = D2LApi(course)
        self.part = part
        self.contentmanager = None
        self.old_content = Path.content(self.course.name, self.part).read_bytes()
        ProgressManager.add(self)

    def check(self):
        elif self.part == "zoom":
            content = ZoomApi.get_content(self.course.id)
            ProgressManager.progress.add_progress(len(self.old_content) + 1000) # set as progress when request done
        else:
            content = self.api.get(self.part)
            ProgressManager.progress.add_progress(1000)
            # Here progress is accumulated during request

        if content != self.old_content or True:
            self.process_changes(content, self.old_content)
        else:
            UserInterface.add_check(0)

    @staticmethod
    def check_notifications():
        last_announ_seen = Path.content("notifications", "notifications").read_text()
        if not last_announ_seen:
            last_announ_seen = datetime.now()
            last_announ_seen = str(last_announ_seen.replace(year=last_announ_seen.year - 1))
            last_announ_seen = last_announ_seen.replace(" ", "T")[:-3] + "Z"

        url_tail = f"?since={last_announ_seen}" if last_announ_seen else ""
        new_announ_url = "https://ufora.ugent.be/d2l/api/lp/1.30/feed/" + url_tail

        content = SessionManager.get(new_announ_url).content
        changed = content != b"[]"

        if changed:
            last_announ = json.loads(content)[0]["Metadata"]["Date"]
            changed = last_announ_seen != last_announ
        if changed:
            Path.content("notification", "notifications").write_text(last_announ)
        return changed

    def process_changes(self, content, old_content):
        from .contentmanager import ContentManager
        from .updatemanager import UpdateManager

        self.contentmanager = ContentManager(content, old_content, self.part, self)
        UpdateManager.process_updates(self.contentmanager)

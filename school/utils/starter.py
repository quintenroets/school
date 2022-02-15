from libs.threading import Threads
from school.content import courseinfo
from school.content.coursemanager import CourseManager
from school.ui.userinterface import UserInterface

from . import notifications


class Starter:
    @staticmethod
    def check_changes():
        courses = courseinfo.get_courses()
        coursemanagers = [
            CourseManager(c, part) for c in courses for part in c.to_check
        ]

        content_threads = Threads([c.check for c in coursemanagers]).start()

        if notifications.check_notifications():
            extra_coursemanagers = [CourseManager(c, "news/") for c in courses]
            coursemanagers += extra_coursemanagers
            extra_content_threads = Threads(
                [c.check for c in extra_coursemanagers]
            ).start()

        UserInterface.show_progres(len(coursemanagers))

        content_threads.join()
        if len(coursemanagers) > len(content_threads.threads):
            extra_content_threads.join()

        new_sections = [
            s
            for c in coursemanagers
            if c.contentmanager
            for s in c.contentmanager.new_topic_sections
        ]
        if new_sections:
            from school.content.outputwriter import OutputWriter

            OutputWriter.write_output_to_html(new_sections)

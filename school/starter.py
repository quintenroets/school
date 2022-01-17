from tbhandler.threading import Threads

from .courseinfo import CourseInfo
from .coursemanager import CourseManager
from .userinterface import UserInterface
from .sessionmanager import SessionManager
from .progressmanager import ProgressManager


class Starter:
    @ staticmethod
    def check_changes():
        courses = CourseInfo.get_courses()
        coursemanagers = [CourseManager(c, part) for c in courses for part in c.to_check]

        content_threads = Threads([c.check for c in coursemanagers])
        if CourseManager.check_notifications():
            extra_coursemanagers = [CourseManager(c, 'news/') for c in courses]
            coursemanagers += extra_coursemanagers
            extra_content_threads = Threads([c.check for c in extra_coursemanagers])

        UserInterface.show_progres(len(coursemanagers))

        content_threads.join()
        if len(coursemanagers) > len(content_threads.threads):
            extra_content_threads.join()

        if new_sections:= [s for c in coursemanagers if c.contentmanager for s in c.contentmanager.new_topic_sections]:
            from .outputwriter import OutputWriter
            OutputWriter.write_output_to_html(new_sections)

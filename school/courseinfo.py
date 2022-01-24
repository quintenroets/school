from . import constants
from .path import Path


class Course:
    def __init__(self, info):
        self.name = info["name"]
        self.id = info["id"]
        self.to_check = ["content/toc"]  # , 'zoom']


class CourseInfo:
    @staticmethod
    def get_courses():
        courses = Path.courses.load()
        if not courses:
            from .coursemaker import CourseMaker

            courses = CourseMaker.make_courses()

        nr = constants.one_course_nr
        courses = courses[nr - 1 : nr] if nr else courses
        courses = sorted(
            courses, key=lambda c: -Path.content(c["name"], "content/toc").size
        )
        courses = [Course(c) for c in courses]
        return courses

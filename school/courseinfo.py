from .assets import Courses
from .path import Path


class CourseInfo:
    @staticmethod
    def get_courses():
        courses = Path.courses.load()
        if not courses or True:
            from .coursemaker import CourseMaker

            courses = CourseMaker.make_courses()

        return Courses.from_dict(courses).courses

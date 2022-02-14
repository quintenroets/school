from school.asset_types.course import Courses
from school.utils.path import Path


def get_courses():
    courses = Path.courses.load()
    if not courses:
        from .coursemaker import CourseMaker

        courses = CourseMaker.make_courses()

    return Courses.from_dict(courses).courses

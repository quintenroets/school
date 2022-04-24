from school.asset_types.course import Courses
from school.utils.path import Path


def get_courses():
    from .coursemaker import CourseMaker  # noqa: autoimport

    courses = Path.courses.load()
    if not courses:

        courses = CourseMaker.make_courses()

    return Courses.from_dict(courses).courses

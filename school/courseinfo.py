from dataclasses import dataclass
from typing import List

from . import constants
from .path import Path


@dataclass(order=True)
class Course:
    name: str
    id: str

    @property
    def to_check(self):
        return ["content/toc"]

    @property
    def sort_index(self):
        return -Path.content(self.name, self.to_check[0]).size


class CourseInfo:
    @staticmethod
    def get_courses():
        courses = Path.courses.load()
        if not courses:
            from .coursemaker import CourseMaker

            courses = CourseMaker.make_courses()

        nr = constants.one_course_nr
        courses = courses[nr - 1 : nr] if nr else courses
        courses = [Course(**c) for c in courses]
        return sorted(courses)

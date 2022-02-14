from dataclasses import dataclass
from typing import List

from school.utils import constants
from school.utils.path import Path

from .base import Item


@dataclass(order=True)
class Course(Item):
    name: str
    id: str

    @property
    def to_check(self):
        return ["content/toc"]  # , "zoom"]

    @property
    def sort_index(self):
        return -Path.content_path(self.name, self.to_check[0]).size


@dataclass
class Courses:
    courses: List[Course]

    @classmethod
    def from_dict(cls, courses):
        if constants.one_course_nr:
            courses = [courses[constants.one_course_nr - 1]]
        return Courses(sorted([Course(**c) for c in courses]))

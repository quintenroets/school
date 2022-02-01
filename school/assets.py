from dataclasses import asdict, dataclass
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
        return -Path.content_path(self.name, self.to_check[0]).size

    def dict(self):
        return asdict(self)


@dataclass
class Courses:
    courses: List[Course]

    @classmethod
    def from_dict(cls, courses):
        if constants.one_course_nr:
            courses = [courses[constants.one_course_nr]]
        return Courses(sorted([Course(**c) for c in courses]))

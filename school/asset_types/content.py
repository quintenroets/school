from dataclasses import dataclass
from typing import List

from school.utils.path import Path

from .ufora import Topic
from .zoom import Recording


@dataclass
class Info:
    order: int
    mtime: int


@dataclass
class Item(Info):
    title: str
    recording_info: Recording = None
    toc_info: Topic = None
    html_content: str = None
    updated: bool = False
    order_changed: bool = False
    url: str = None
    dest: Path = None

    @property
    def changed(self):
        return self.toc_info is None or not self.order_changed


@dataclass
class Section(Info):
    items: List[Item]
    titles: List[str]
    order_changed: bool = False

    @property
    def changed(self):
        return any([it.changed for it in self.items])

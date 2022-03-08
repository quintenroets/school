from dataclasses import dataclass
from typing import List, Union

from school.utils.path import Path

from .news import NewsItem
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
    announ_info: NewsItem = None
    html_content: Union[str, List[NewsItem]] = None
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

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from school.utils import timeparser

from .base import Item


@dataclass
class Description:
    Text: str
    Html: str


@dataclass
class ContentItem(Item):
    Title: str


@dataclass
class HTMLItem(ContentItem):
    content: str


@dataclass
class UforaItem(ContentItem):
    IsHidden: bool
    LastModifiedDate: str

    @property
    def mtime(self):
        return timeparser.parse(self.LastModifiedDate)


@dataclass
class TreeItem(UforaItem):
    IsLocked: bool
    Description: Description
    SortOrder: int
    StartDateTime: Optional[str]
    EndDateTime: Optional[str]
    PacingStartDate: Optional[str]
    PacingEndDate: Optional[str]
    DefaultPath: Optional[str]

    def __post_init__(self):
        self.SortOrder += 1000  # make sure sort order always positive


@dataclass
class ContentTree(Item):
    Modules: Optional[List[Module]] = field(default_factory=list)
    Topics: Optional[List[Topic]] = field(default_factory=list)


@dataclass
class Module(TreeItem):
    ModuleId: int
    Modules: List[Module]
    Topics: List[Topic]


@dataclass
class Topic(TreeItem):
    IsExempt: bool
    IsBroken: bool
    ActivityId: str | None
    CompletionType: int
    TopicId: int
    Identifier: str
    TypeIdentifier: str
    Bookmarked: bool
    Unread: bool
    Url: str
    ToolId: Optional[int]
    ToolItemId: Optional[int]
    ActivityType: int
    GradeItemId: Optional[int]

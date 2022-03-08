from dataclasses import dataclass, field
from typing import List, Optional

from .ufora import Item, UforaItem


@dataclass
class Body:
    Text: str
    Html: str


@dataclass
class Attachment:
    FileId: int
    FileName: str
    Size: int


@dataclass
class NewsItem(UforaItem):
    Id: int
    Attachments: List[Attachment]
    CreatedBy: int
    CreatedDate: str
    LastModifiedBy: Optional[int]
    Body: Body
    StartDate: str
    EndDate: Optional[str]
    IsGlobal: bool
    IsPublished: bool
    ShowOnlyInCourseOfferings: bool
    IsAuthorInfoShown: bool

    def __post_init__(self):
        self.order = 9999


@dataclass
class News(Item):
    items: List[NewsItem] = field(default_factory=list)

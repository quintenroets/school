from dataclasses import dataclass
from typing import List, Optional

from .base import Item


@dataclass
class Recording(Item):
    meetingId: str
    meetingNumber: str
    accountId: str
    topic: str
    startTime: str
    hostId: str
    duration: int
    status: int
    hostEmail: str
    totalSize: int
    recordingCount: int
    disabled: int
    timezone: str
    totalSizeTransform: str
    createTime: Optional[str]
    modifyTime: Optional[str]
    key: str
    publish: int
    value: str
    recordingFiles: Optional[str]
    listStartTime: str
    enableAndPublished: bool
    enable: bool
    student: bool
    published: bool


@dataclass
class Result(Item):
    pageNum: int
    sortBy: Optional[str]
    sortAsc: bool
    pageSize: int
    total: int
    list: List[Recording]
    fromIndex: int
    toIndex: int


@dataclass
class Recordings(Item):
    status: Optional[bool] = None
    result: Optional[Result] = None

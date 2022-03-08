from enum import Enum
from typing import List

from school.asset_types.content import Item, Section
from school.asset_types.news import News, NewsItem
from school.asset_types.ufora import ContentTree, Module, Topic
from school.asset_types.zoom import Recordings
from school.utils import timeparser
from school.utils.path import Path


def extract_recording_differences(content: Recordings, old_content: Recordings):
    recordings = content.result and content.result.list or []
    recordings.reverse()  # most recent highest order
    old_recordings = old_content.result and old_content.result.list or []
    old_recordings_ids = {r.id for r in old_recordings}

    new_recordings = [
        (i, r)
        for i, r in enumerate(recordings)
        if r.meetingId not in old_recordings_ids
    ]
    items = []
    for i, r in new_recordings:
        mtime = timeparser.parse(r.startTime, "%Y-%m-%d %H:%M:%S")
        title = f"Lecture {i+1} - {r.topic}"
        item = Item(order=i + 11, mtime=mtime, title=title, recording_info=r)
        items.append(item)

    sections = (
        [Section(order=10, mtime=items[-1].mtime, titles=["Recordings"], items=items)]
        if items
        else []
    )
    return sections


def extract_news_differences(content: News, old_content: News):
    old_items = {it.Id: it for it in old_content.items}
    items = []
    for it in content.items:
        if it.Id not in old_items or old_items[it.Id].mtime != it.mtime:
            item = Item(order=9999, mtime=it.mtime, title=it.Title, announ_info=it)
            items.append(item)

    if items:
        items[0].html_content = content.items

    sections = (
        [
            Section(
                order=9999,
                mtime=items[-1].mtime,
                titles=["Announcements.html"],
                items=items,
            )
        ]
        if items
        else []
    )
    return sections


def extract_tree_differences(content: ContentTree, old_content: ContentTree):
    sections = []
    queue = [(content, old_content, [])]

    while queue:
        module, module_old, titles = queue.pop(0)
        old_topics = {t.TopicId: t for t in module_old.Topics}

        items = []
        for topic in module.Topics:
            old_topic: Topic = old_topics.get(topic.TopicId)
            if (
                old_topic is None
                or old_topic.mtime != topic.mtime
                or old_topic.SortOrder != topic.SortOrder
            ):
                item = Item(
                    order=topic.SortOrder,
                    mtime=topic.mtime,
                    title=topic.Title,
                    toc_info=topic,
                    url=topic.Url,
                )

                if old_topic is not None and old_topic.mtime == topic.mtime:
                    item.order_changed = True
                elif old_topic is not None:
                    item.updated = True
                items.append(item)

        if isinstance(module, Module):
            html = module.Description.Html
            if (
                html
                and isinstance(module_old, ContentTree)
                or module.mtime != module_old.mtime
            ):
                item = Item(
                    order=9, mtime=module.mtime, title="Info.html", html_content=html
                )
                items.append(item)

            section = Section(
                order=module.SortOrder, mtime=module.mtime, items=items, titles=titles
            )
            sections.append(section)

            if (
                not isinstance(module_old, Module)
                or module_old.SortOrder != module.SortOrder
            ):
                section = Section(
                    order=module.SortOrder,
                    mtime=module.mtime,
                    items=[],
                    titles=titles,
                    order_changed=True,
                )
                sections.append(section)

        new_modules: List[Module] = [
            m for m in module.Modules if m not in module_old.Modules
        ]
        for submodule in new_modules:
            old_submodules = [
                m for m in module_old.Modules if m.ModuleId == submodule.ModuleId
            ]
            old_submodule = old_submodules[0] if old_submodules else ContentTree()
            queue.append((submodule, old_submodule, titles + [submodule.Title]))
    return sections


def extract_differences(content, content_old):
    extractors = {
        ContentTree: extract_tree_differences,
        News: extract_news_differences,
        Recordings: extract_recording_differences,
    }
    for asset_type, extractor in extractors.items():
        if isinstance(content, asset_type):
            return extractor(content, content_old)


class ContentType(Enum):
    announ = "Announcements"
    zoom = "Zoom"
    tree = "Tree"


class SectionInfo(Section):
    def __init__(self, section, coursemanager):
        super().__init__(**section.__dict__)
        self.coursemanager = coursemanager
        self.downloadprogress = None

        self.content_type = ContentType.tree
        if any([it.recording_info for it in self.items]):
            self.content_type = ContentType.zoom
        elif section.titles == ["Announcements.html"]:
            self.content_type = ContentType.announ

        self.dest = Path.school.subpath(self.coursemanager.course.name, *self.titles)
        for it in self.items:
            if it.toc_info and it.toc_info.TypeIdentifier == "File":
                it.title += "." + it.toc_info.Url.split(".")[-1]
            it.dest = self.dest / it.title

    @property
    def tree_item(self):
        return self.content_type == ContentType.tree

    @property
    def announ(self):
        return self.content_type == ContentType.announ

    @property
    def zoom(self):
        return self.content_type == ContentType.zoom


class ContentManager:
    def __init__(self, content, content_old, part, coursemanager):
        self.content_bytes = content

        if part == "content/toc":
            cls = ContentTree
        elif part == "news/":
            cls = News
        else:
            cls = Recordings

        self.part = part
        self.content = cls.from_bytes(content)
        self.content_old = cls.from_bytes(content_old)

        sections = extract_differences(self.content, self.content_old)

        self.sections: List[SectionInfo] = [
            SectionInfo(s, coursemanager) for s in sections
        ]
        self.new_topic_sections = []
        self.coursemanager = coursemanager

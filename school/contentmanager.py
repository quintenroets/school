import json

from .path import Path
from . import timeparser


class ContentManager:
    def __init__(self, content, content_old, part, coursemanager):
        self.content_bytes = content

        self.content = json.loads(content)
        self.content_old = json.loads(content_old or '{}')

        self.coursemanager = coursemanager
        self.sections = []

        if 'content' in part:
            self.get_updates(self.content, self.content_old)
        else:
            parts = {
                'news': {'subkeys': [], 'id': 'Id', 'sections': ['Announcements']},
                'zoom': {'subkeys': ['result', 'list'], 'id': 'meetingId', 'sections': ['Zoom']}
            }
            for p in parts:
                if p in part:
                    part_info = parts[p]
                    self.parse_content(*part_info['subkeys'])
                    self.extract_new_items(self.content, self.content_old, part_info['id'], part_info['sections'])

    def parse_content(self, *keys):
        for k in keys:
            self.content = self.content[k]
            self.content_old = self.content_old.get(k, {})

    def get_updates(self, content, content_old):
        queue = [(content, content_old, [], 0)]
        while queue:
            content, content_old, titles, _ = queue.pop(0)
            for key, subskey in [('ModuleId', 'Modules'), ('TopicId', 'Topics')]:
                subcontent = content.get(subskey, [])
                subcontent_old = content_old.get(subskey, [])
                queue += self.extract_new_items(subcontent, subcontent_old, key, titles, content)

    def extract_new_items(self, items, items_old, key, titles, content=None):
        items_old = {m[key]: m for m in items_old}
        recurse_changes = []
        changes = []
        for i, item in enumerate(items):
            item_old = items_old.get(item[key], {})
            if item != item_old:
                item_info = (item, item_old, titles + [item.get('Title', '')], len(items) - i)
                recurse_changes.append(item_info)
                difs = [k for k in ['LastModifiedDate', 'SortOrder', key] if item.get(k) != item_old.get(k)]
                if difs or not item_old:
                    item['difs'] = difs
                    item['real_difs'] = [d for d in difs if d != 'SortOrder']
                    changes.append(item_info)

        if changes and (key != 'ModuleId' or (content and not content.get('Topics'))):
            self.sections.append(Section(titles, changes, content, self.coursemanager))
        return recurse_changes

class Section:
    def __init__(self, titles, items, content, coursemanager):
        self.coursemanager = coursemanager
        self.titles = titles

        self.tree_item = not titles or titles[0] not in ['Announcements', 'Zoom']
        self.announ = titles and titles[0] == 'Announcements'
        self.zoom = titles and titles[0] == 'Zoom'
        if self.zoom:
            self.titles = ['Lectures']

        self.dest = Path.dest(coursemanager.course.name, self.titles)
        self.downloadprogress = None

        self.only_subfolders = self.tree_item and not content.get('Topics')

        self.items = [Item(it, len(items) - i, self) for i, it in enumerate(items)]
        self.content = Content(content, 1, self) if content else self.items[0]
        self.time = content and content.get('LastModifiedDate') and timeparser.parse(content['LastModifiedDate'], '')
        self.changed = any([i.changed for i in self.items])
        
        if content and (html:= content.get('Description', {}).get('Html')):
            html_item = Item((content, {}, titles, len(items) + 1), len(items) + 1, self)
            html_item.dest = self.dest / 'Info.html'
            html_item.order = 1
            html_item.changed = not items or self.changed
            if html_item.changed:
                self.changed = True
            html_item.html = html
            if self.only_subfolders:
                self.items = [html_item]
                self.only_subfolders = False
            else:
                self.items.append(html_item)

        if self.announ:
            self.content.order = 9999

        self.order_changed = any([i.order_changed for i in self.items])


class Content:
    def __init__(self, item, number, section):
        self.__dict__.update(item)
        self.time = item.get('LastModifiedDate')
        self.order = item.get('SortOrder') + 1000 if 'SortOrder' in item else 1
        if section.zoom:
            self.order = number + 5
            self.time = timeparser.parse(item.get('startTime'), '%Y-%m-%d %H:%M:%S')


class Item(Content):
    def __init__(self, item_info, number, section):
        item, old_item, titles, number = item_info
        super(Item, self).__init__(item, number, section)

        self.section = section

        self.updated = bool(old_item)
        self.titles = titles

        self.is_folder = 'ModuleId' in item
        self.html = None

        self.title = item.get('Title', 'No title')
        if 'Url' in item and item.get('TypeIdentifier') == 'File':
            self.title += item['Url'][item['Url'].rfind('.'):]
        if self.section.zoom:
            self.title = f'Lecture {number}'

        self.dest: Path = section.dest / self.title.replace('/', '_')

        self.changed = bool(item.get('real_difs'))
        self.order_changed = 'difs' in item and 'SortOrder' in item['difs']

    def __copy__(self):
        item_info = (self.__dict__, {}, self.titles, self.order - 5)
        return Item(item_info, self.order - 5, self.section)

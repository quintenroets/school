from bs4 import BeautifulSoup
from json import loads

from libs.parser import Parser
from libs.shortcutmaker import ShortcutMaker

from . import constants
from .sessionmanager import SessionManager
from .path import Path


class CourseMaker:
    shortcutmaker = ShortcutMaker()

    @staticmethod
    def make_courses():
        url = 'https://ufora.ugent.be/d2l/lp/courseSelector/6606/InitPartial?_d2l_prc%24headingLevel=2&_d2l_prc%24scope=&_d2l_prc%24hasActiveForm=false&isXhr=true&requestId=1'
        content = SessionManager.get(url).content
        content = loads(Parser.between(content, b'while(1);'))['Payload']['Html']
        page = BeautifulSoup(content, 'html.parser')

        course_tags = page.findAll('li', {'class': 'vui-selected'})
        courses = [CourseMaker.make_course_info(l) for l in course_tags]
        courses = sorted(courses, key=lambda item: item['name'].lower())

        course_nr = 1
        for course in courses:
            CourseMaker.make_course(course, course_nr)
            course_nr += 1

        CourseMaker.shortcutmaker.set_shortcuts()

        calendar_file = Path.school / 'Calendar.html'
        calendar_content = '<script>window.location.href='https://ufora.ugent.be/d2l/le/calendar/000000';</script>'
        calendar_file.write_text(calendar_content)

        if constants.update_content:
            Path.courses.save(courses)

        return courses

    @staticmethod
    def make_course(course, course_nr):
        course_folder = Path.school / course['name']
        course_folder.mkdir(parents=True, exist_ok=True)
        
        name = course['name'].replace(' ', '_').replace("'", '')
        ufora_url = f'https://ufora.ugent.be/d2l/lp/auth/saml/login?' \
                    f'target=%2fd2l%2fle%2fcontent%2f{course["id"]}%2fHome'

        # 10, 11, 12 -> 1, 2, 3, ..
        # 67, 68, 69 -> F1, F2, F3, ..
        # course_folder = course_folder.replace(' ', '\\ ').replace(''', '\\'')
        shortcuts = {
            # f'dolphin {course_folder}': f'Mod4 'c:{9 + course_nr}'', # Windows-key + 1
            
            f'checkpoint {name}':
                f'control "c:{9 + course_nr}"',
            
            f'checkpoint choose {name}':
                f'control shift "c:{9 + course_nr}"',
            
            f'chromium {ufora_url}':
                f'control "c:{119 + course_nr}"', # ctrl f1
            
            '': ''
        }
        
        for target, hotkey in shortcuts.items():
            CourseMaker.shortcutmaker.make_shortcut(hotkey, target)

    @staticmethod
    def make_course_info(listitem):
        course_tag = listitem.find('a')

        name = course_tag.text.split(' - ')[1]
        id_ = course_tag.get('href').split('/')[-1]
        return {'name': name, 'id': id_}

    @staticmethod
    def get_id(course):
        return course['url'].replace('https://ufora.ugent.be/d2l/le/content/', '').replace('/Home', '')

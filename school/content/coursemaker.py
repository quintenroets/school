import json

from bs4 import BeautifulSoup
from libs.shortcutmaker import ShortcutMaker

from school.asset_types.course import Course
from school.clients.session import session
from school.utils import constants
from school.utils.path import Path


class CourseMaker:
    @staticmethod
    def make_courses():
        url = (
            "https://ufora.ugent.be/d2l/lp/courseSelector/6606/InitPartial?_d2l_prc%24headingLevel=2"
            "&_d2l_prc%24scope=&_d2l_prc%24hasActiveForm=false&isXhr=true&requestId=1"
        )
        content = session.get(url).text.replace("while(1);", "")
        html = json.loads(content)["Payload"]["Html"]
        parsed_html = BeautifulSoup(html, "html.parser")
        courses = CourseMaker.parse_courses(parsed_html)

        CourseMaker.make_shortcuts(courses)

        calendar_file = Path.school / "Calendar.html"
        calendar_file.text = '<script>window.location.href="https://ufora.ugent.be/d2l/le/calendar/000000";</script>'

        for course in courses:
            (Path.school / course.name).mkdir(parents=True, exist_ok=True)

        courses_dict = [c.dict() for c in courses]
        if constants.update_content:
            Path.courses.content = courses_dict

        return courses_dict

    @staticmethod
    def parse_courses(html):
        courses = []
        for course_tag in html.findAll("li", {"class": "vui-selected"}):
            href_tag = course_tag.find("a")
            course = Course(
                name=href_tag.text.split(" - ")[1],
                id=href_tag.get("href").split("/")[-1],
            )
            courses.append(course)

        courses = sorted(courses, key=lambda item: item.name.lower())
        return courses

    @staticmethod
    def make_shortcuts(courses):
        shortcutmaker = ShortcutMaker()
        for i, course in enumerate(courses):
            name = course.name.replace(" ", "_").replace("'", "")
            url = f"https://ufora.ugent.be/d2l/lp/auth/saml/login?target=%2fd2l%2fle%2fcontent%2f{course.id}%2fHome"

            shortcuts = {
                f"checkpoint {name}": f'control "c:{10 + i}"',
                f"checkpoint choose {name}": f'control shift "c:{10 + i}"',  # 10, 11, 12 -> 1, 2, 3, ..
                f"xdg-open {url}": f'control "c:{67 + i}"',  # 67, 68, 69 -> F1, F2, F3, ..
                "": "",
            }

            for target, hotkey in shortcuts.items():
                shortcutmaker.add_shortcut(hotkey, target)

        shortcutmaker.save_shortcuts()

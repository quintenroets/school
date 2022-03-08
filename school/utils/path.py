import plib


class BasePath(plib.Path):
    def subpath(self, *parts):
        new_parts = []
        for p in parts:
            for i in range(5, 0, -1):
                p = p.replace(">" * i + " ", "")
            new_parts.append(p)
        return super().subpath(*new_parts)


root = BasePath(__file__).parent.parent


class Path(BasePath):
    templates = root / "templates"

    assets = BasePath.assets / root.name
    courses = assets / "courses" / "courses"
    content_assets = assets / "content"

    school = BasePath.docs / "School"
    content_folder_name = "Content"

    @staticmethod
    def cookies(name="cookies"):
        return Path.assets / "cookies" / name

    @staticmethod
    def dest(course_name, titles):
        return Path.school.subpath(course_name, *titles)

    @staticmethod
    def content_path(course, sort):
        return Path.content_assets.subpath(sort, course).with_suffix(".txt")

    @staticmethod
    def content_folder(path):
        return path / Path.content_folder_name

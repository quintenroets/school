from plib import Path as BasePath

root = BasePath(__file__).parent


class Path(BasePath):
    templates = root / "templates"

    assets = BasePath.assets / root.name
    courses = assets / "courses" / "courses"

    school = BasePath.docs / "School"
    content_folder_name = "Content"

    trusted = True

    @staticmethod
    def cookies(name="cookies"):
        return Path.assets / "cookies" / name

    @staticmethod
    def dest(course, titles):
        path = Path.school.subpath(course, *titles)
        if "Announcements" not in titles:
            path.mkdir(parents=True, exist_ok=True)

        return path

    @staticmethod
    def content_path(course, sort):
        return Path.assets.subpath(sort, course).with_suffix(".txt")

    @staticmethod
    def content_folder(path):
        return path / Path.content_folder_name

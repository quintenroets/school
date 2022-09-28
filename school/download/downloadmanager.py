import threading

import cli
from school.content.contentmanager import Item, SectionInfo
from school.utils.path import Path

from .videomanager import VideoManager


def convert_office(item: Item):
    office_extensions = [".pptx", ".ppt", ".doc"]
    if item.dest.suffix in office_extensions:
        cli.run("unoconv -f pdf", item.dest)
        item.dest.unlink()
        item.dest = item.dest.with_suffix(".pdf")


class DownloadManager:
    mutex = threading.Lock()

    @staticmethod
    def make_section(section: SectionInfo):
        if not section.announ:
            section.dest.mkdir(parents=True, exist_ok=True)
        DownloadManager.update_order(section)
        section.dest.mtime = section.mtime

    @staticmethod
    def update_order(section: SectionInfo):
        if section.dest:
            if not section.announ:
                section.dest.mkdir(parents=True, exist_ok=True)
            section.dest.tag = section.order

    @staticmethod
    def process_downloads(section):
        DownloadManager.make_section(section)

        if not section.announ:
            with DownloadManager.mutex:
                DownloadManager.process_content_downloads(section)

    @staticmethod
    def process_content_downloads(section: SectionInfo):
        # first set tags for correct order
        for item in section.items:
            if item.dest:
                if item.dest.exists():
                    if section.coursemanager.course.name not in (
                        "Mobile and Broadband Access Networks",
                        "Information Security",
                    ):
                        convert_office(item)

                    item.dest.mtime = item.mtime
                    item.dest.tag = item.order
                else:
                    orig_name = item.dest.stem
                    count = 1
                    item.dest = item.dest.with_stem(f"{orig_name}_view{count}")
                    while item.dest.exists():
                        item.dest.mtime = item.mtime
                        item.dest.tag = item.order
                        count += 1
                        item.dest = item.dest.with_stem(f"{orig_name}_view{count}")

                if item.dest.suffix == ".zip":
                    new_dest = item.dest.with_suffix("")
                    DownloadManager.extract_zip(item.dest, new_dest, remove_zip=True)
                    item.dest = new_dest

        VideoManager.process_videos(section.dest)
        DownloadManager.copy_to_parents(section.dest)

    @staticmethod
    def copy_to_parents(folder: Path):
        files_to_copy = DownloadManager.get_files_to_copy(folder)

        for parent in DownloadManager.get_parents(folder):
            for file, file_full in files_to_copy:
                DownloadManager.make_shortcut(file, file_full, parent)
            VideoManager.process_videos(parent)
            parent.mtime = folder.mtime

    @staticmethod
    def get_files_to_copy(folder: Path):
        skip = ["Videos.html", "Info.html"]

        to_copy = []
        if folder.exists():
            for filename in folder.iterdir():
                if (
                    filename.name not in skip
                    and not filename.is_dir()
                    and not filename.is_symlink()
                    and filename.tag
                ):
                    couple = (filename.name, filename)
                    to_copy.append(couple)

        return to_copy

    @staticmethod
    def get_parents(folder: Path):
        content_folder = Path.content_folder(folder)
        parents = [content_folder] if content_folder.exists() else []
        while (folder := folder.parent) != Path.school.parent:
            parent_content = Path.content_folder(folder)
            parents.append(parent_content)
            parent_content.mkdir(parents=True, exist_ok=True)
            parent_content.tag = 0
        return parents

    @staticmethod
    def make_shortcut(file, target, folder: Path):
        shortcut_name = folder / file
        if shortcut_name.exists():
            shortcut_name.unlink()
        try:
            shortcut_name.symlink_to(target)
        except FileExistsError:
            pass

    @staticmethod
    def extract_all_zips(source: Path, dest: Path):
        for path in source.iterdir():
            path.check_zip()

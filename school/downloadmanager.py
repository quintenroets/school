from zipfile import ZipFile
import threading

from libs.cli import Cli

from .videomanager import VideoManager

from .contentmanager import Section
from .path import Path


class DownloadManager:
    mutex = threading.Lock()

    @staticmethod
    def make_section(section: Section):
        if not section.announ:
            section.dest.mkdir(parents=True, exist_ok=True)
        section.dest.time = section.content.time
        DownloadManager.update_order(section)

    @staticmethod
    def update_order(section):
        if section.dest and section.content and section.content.order:
            section.dest.tag = section.content.order

    @staticmethod
    def process_downloads(section):
        DownloadManager.make_section(section)

        if not section.announ:
            DownloadManager.process_content_downloads(section)

    @staticmethod
    def process_content_downloads(section: Section):
        # first set tags for correct order
        for item in section.items:
            if item.dest:
                if item.dest.exists():
                    office_extentions = [".pptx", ".doc"]
                    if item.dest.suffix in office_extentions:
                        command = f"unoconv -f pdf '{item.dest}'"
                        Cli.run(command)
                        item.dest.unlink()
                        item.dest = item.dest.with_suffix(".pdf")

                    item.dest.time = item.time
                    if item.order:
                        item.dest.tag = item.order
                else:
                    orig_name = item.dest.stem
                    count = 1
                    item.dest = item.dest.with_stem(f"{orig_name}_view{count}")
                    while item.dest.exists():
                        item.dest.time = item.time
                        if item.order:
                            item.dest.tag = item.order
                        count += 1
                        item.dest = item.dest.with_stem(f"{orig_name}_view{count}")

        VideoManager.proces_videos(section.dest)
        DownloadManager.copy_to_parents(section.dest)

    @staticmethod
    def copy_to_parents(folder):
        files_to_copy = DownloadManager.get_files_to_copy(folder)

        for parent in DownloadManager.get_parents(folder):
            for file, file_full in files_to_copy:
                DownloadManager.make_shortcut(file, file_full, parent)
            VideoManager.proces_videos(parent)

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
        while (folder := folder.parent) != Path.school:
            parent_content = Path.content_folder(folder)
            parents.append(parent_content)
            parent_content.mkdir(parents=True, exist_ok=True)
            parent_content.tag = 0
        return parents

    @staticmethod
    def make_shortcut(file, target, folder: Path):
        shortcut_name = folder / file
        with DownloadManager.mutex:
            if shortcut_name.exists():
                shortcut_name.unlink()
            try:
                shortcut_name.symlink_to(target)
            except FileExistsError:
                pass

    @staticmethod
    def extract_all_zips(source: Path, dest: Path):
        if source.exists():
            for path in source.iterdir():
                if path.suffix == ".zip":
                    DownloadManager.extract_zip(path, dest)

    @staticmethod
    def extract_zip(zipfile: Path, folder: Path, remove_zip=True):
        folder.mkdir(parents=True, exist_ok=True)
        with ZipFile(zipfile) as zip_ref:
            zip_ref.extractall(path=folder)
        
        for path in folder.iterdir():
            path.tag = zipfile.tag
        if remove_zip:
            zipfile.unlink()

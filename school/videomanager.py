import mimetypes
import urllib.parse
from datetime import datetime

import cli

from .path import Path


class VideoManager:
    template = (Path.templates / "video.html").read_text()
    template_two = (Path.templates / "two_video.html").read_text()

    @staticmethod
    def process_videos(folder: Path, video_folder="Videos"):
        videos = {}
        for filename in folder.iterdir():
            filetype = mimetypes.guess_type(filename)[0]
            if filetype and filetype.startswith("video"):
                key = filename.with_stem(filename.stem.split("_view")[0])
                videos[key] = videos.get(key, []) + [filename]

        if videos:
            VideoManager.process_new_videos(folder, videos, video_folder)

    @staticmethod
    def process_new_videos(folder: Path, videos, video_folder):
        videos_folder = folder / video_folder
        videos_folder.mkdir(parents=True, exist_ok=True)
        videos_folder.tag = 1

        fileslist = [
            VideoManager.make_html_video(folder, videos_folder, video, items)
            for video, items in videos.items()
        ]
        fileslist = [f for f in fileslist if f[0].exists()]
        VideoManager.make_index(fileslist, folder, video_folder)

    @staticmethod
    def make_html_video(
        folder: Path, videos_folder, video: Path, items: list[Path], video_url=None
    ):
        already_exist = False

        if video_url:
            filename_video = video_url
            filename_html = (video.parents / videos_folder / video.name).with_suffix(
                ".html"
            )
        else:
            filename_video = items[0]
            filename_html = videos_folder / video.with_suffix(".html").name
            already_exist = filename_video.is_symlink()

        if already_exist:  # html file already exists
            filename_video = filename_video.resolve()
            filename_html = (
                filename_video.parent / "Videos" / video.with_suffix(".html").name
            )
        else:
            content = (
                VideoManager.template if len(items) == 1 else VideoManager.template_two
            )
            replacements = {
                "**SOURCENAME**": items[0],
                "**SOURCENAME1**": items[0],
                "**SOURCENAME2**": items[1] if len(items) > 1 else "",
                "**TEMPLATES**": Path.templates,
            }
            for k, v in replacements.items():
                v = urllib.parse.quote(str(v))
                content = content.replace(k, v)
            Path(filename_html).write(content)
            filename_html.mtime = filename_video.mtime
            filename_html.tag = filename_video.tag

        return filename_video, filename_html

    @staticmethod
    def get_order(filename: Path, use_tags=False):
        order = (filename.tag or "") + str(filename) if use_tags else filename.mtime
        return order

    @staticmethod
    def make_index(fileslist, folder: Path, video_folder):
        fileslist = sorted(fileslist, key=lambda f: VideoManager.get_order(f[0]))
        filename = (folder / video_folder).with_suffix(".html")

        template_folder = "/".join(Path.templates.parts)
        css = f'<link href="file://{template_folder}/video_index.css" rel="stylesheet" />\n'
        js = f'<script src="file://{template_folder}/index_script.js"></script>\n'
        body_in = f"""<body style="background-image: url('file://{template_folder}/background_index.jpg')">"""
        body_out = f"</body>"
        content = "\n".join([VideoManager.video_tag(files) for files in fileslist])
        content = css + js + body_in + content + body_out
        Path(filename).write(content)
        filename.tag = 9999

    @staticmethod
    def video_tag(files):
        filename_video, filename_html = files
        name = filename_video.stem.split("_view")[0].replace("_", "   ")
        duration_tag = VideoManager.get_duration_tag(filename_video)
        time_tag = VideoManager.get_time_tag(filename_video)
        filename_html = urllib.parse.quote(str(filename_html))
        return f"""<h2><a href='{filename_html}' style="text-decoration: none" target = "_blanck
        ">{name}<small>{duration_tag + time_tag}</small></a></h2><hr>"""

    @staticmethod
    def get_duration_tag(video):
        milliseconds = cli.get(f'mediainfo --Inform="Video;%Duration%"', video)
        # Some durations are in float format
        seconds = int(float(milliseconds)) // 1000

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        hours_str = str(int(hours))
        minutes_str = str(minutes)
        if hours:
            minutes_str = minutes_str.zfill(2)
        seconds_str = str(seconds).zfill(2)

        duration_string = minutes_str + ":" + seconds_str
        if hours:
            duration_string = hours_str + ":" + duration_string

        tag = "&ensp;(" + duration_string + ")"
        return tag

    @staticmethod
    def get_time_tag(video: Path):
        time = datetime.fromtimestamp(video.mtime).strftime("%d/%m/%Y - %H:%M")
        tag = "&ensp;[" + time + "]"
        return tag


def main():
    VideoManager.process_videos(Path.cwd())


if __name__ == "__main__":
    main()

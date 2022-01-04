from libs.cli import Cli

from .path import Path
from .videomanager import VideoManager


def main():
    to_merge_dict = {}
    for filename in Path.school.rglob("*_view*.mp4"):
        dest = filename.with_stem(filename.stem.split("_view")[0])
        if dest not in to_merge_dict:
            to_merge_dict[dest] = []
        to_merge_dict[dest].append(filename)
    for dest, sources in to_merge_dict.items():
        merge(dest, sources)
        VideoManager.proces_videos(dest.parent)
        return

def merge(dest, sources):
    merge_command = " ".join([
        "yes | ffmpeg",
        "".join([f"-i '{d}' " for d in sources]),
        "-filter_complex hstack",
        #"-preset ultrafast"
        f"'{dest}'"
    ])
    Cli.run(merge_command)
    for source in sources:
        source.unlink()


if __name__ == "__main__":
    main()

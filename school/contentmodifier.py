import cli
import gui
from school.path import Path


def main():
    folders = {f.stem: f for f in Path.content_assets.iterdir()}
    sort_folder = gui.ask("Choose content sort", folders)

    if sort_folder:
        filenames = {f.stem: f for f in sort_folder.iterdir()}
        filename: Path = gui.ask("Choose course", filenames)

        if filename:
            with filename.with_suffix(".yaml") as tempfile:
                tempfile.content = filename.json
                cli.urlopen(tempfile)
                input("Press enter when you are ready")
                filename.json = tempfile.content


if __name__ == "__main__":
    main()

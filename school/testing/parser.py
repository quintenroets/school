import json

from libs.cli import Cli
from libs.gui import Gui
from school.path import Path


class Parser:
    @staticmethod
    def start():
        sorts = ["content_toc", "zoom"]
        sort = Gui.ask("Choose content sort", sorts)
        if sort:
            folder = Path.assets / sort
            filenames = {f.stem: f for f in folder.glob("*.txt")}
            filename: Path = Gui.ask("Choose course", filenames)

            if filename:
                content = filename.read_bytes()
                content = json.loads(content)

                tempfile = filename.with_suffix(".yaml")
                tempfile.save(content)
                Cli.run(f"kate '{tempfile}'")
                input("Press enter when you are ready")
                content = tempfile.load()
                tempfile.unlink()

                filename.write(
                    json.dumps(content)
                )
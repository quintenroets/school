import cli

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
                tempfile = filename.with_suffix(".yaml")
                tempfile.content = filename.json
                
                cli.urlopen(tempfile)
                input("Press enter when you are ready")
                
                filename.json = tempfile.content
                tempfile.unlink()

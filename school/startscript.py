from sys import argv

from libs.timer import Timer
from libs.errorhandler import ErrorHandler

from .progressmanager import ProgressManager


def main():
    with ErrorHandler(), Timer():
        if len(argv) == 1:
            with ProgressManager():
                from .starter import Starter
                Starter.check_changes()
        else:
            from .testing.parser import Parser
            Parser.start()


if __name__ == "__main__":
    main()


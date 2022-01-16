import sys
import tbhandler

tbhandler.install()

from .progressmanager import ProgressManager


def main():
    if len(sys.argv) == 1:
        with ProgressManager():
            from .starter import Starter
            Starter.check_changes()
    else:
        from .testing.parser import Parser
        Parser.start()


if __name__ == '__main__':
    main()


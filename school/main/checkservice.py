import time

from ..clients import session
from ..utils.starter import Starter


def main():
    hours = 2
    seconds = hours * 60 ** 2
    while True:
        time.sleep(seconds)
        session.check_login()
        Starter.check_changes()


if __name__ == "__main__":
    main()

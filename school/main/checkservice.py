import time

from school.utils.starter import Starter


def main():
    hours = 2
    seconds = hours * 60 ** 2
    while True:
        time.sleep(seconds)
        Starter.check_changes()


if __name__ == "__main__":
    main()

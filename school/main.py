from .progressmanager import ProgressManager


def main():
    with ProgressManager():
        from .starter import Starter

        Starter.check_changes()


if __name__ == "__main__":
    main()

from school.ui.progressmanager import ProgressManager


def main():
    with ProgressManager():
        from school.utils.starter import Starter  # noqa: autoimport

        Starter.check_changes()


if __name__ == "__main__":
    main()

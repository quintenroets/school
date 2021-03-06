import cli
from setuptools import find_packages, setup

NAME = "school"


def read(filename):
    try:
        with open(filename) as fp:
            content = fp.read().split("\n")
    except FileNotFoundError:
        content = []
    return content


setup(
    author="Quinten Roets",
    author_email="quinten.roets@gmail.com",
    description="",
    name=NAME,
    version="1.0",
    packages=find_packages(),
    setup_requires=read("setup_requirements.txt"),
    install_requires=read("requirements.txt"),
    package_data={"school": ["templates/*"]},
    entry_points={
        "console_scripts": [
            "school = school.main.main:main",
            "videomanager = school.download.videomanager:main",
            "schoolcontent = school.content.contentmodifier:main",
            "schoolcheck = school.main.checkservice:main",
        ]
    },
)


cli.install(*read("packages.txt"))

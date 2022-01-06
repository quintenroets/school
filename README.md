# School
Automatically download all your course materials and keep track of your progress

For students at Ghent University or other Ufora users

## Installation

```shell
pip install git+https://github.com/quintenroets/school
```
Developed for Linux OS

## Usage
1) Pin the courses you want to sync automatically in the Ufora web browser (click on the pin icon)
2) replace email and password in constants.py with your own email and password
3) Run in cli

```shell
school
```
to check for new items and download them

The script can download:
* Ufora course content
* Ufora announcements
* Opencast paella lecture recordings
* Zoom lecture recordings

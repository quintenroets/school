# School
Package especially developed for students at Ghent University

Automatically download all your course materials and keep track of your progress
developed for Linux OS

## Installation

```shell
pip install git+https://github.com/quintenroets/school
```

## Usage
1) Pin the courses you want to sync automatically in the Ufora web browser (click on the pin icon)
2) replace email and password in constants.py with your own email and password
Run 

```shell
school
```
to check for new items and download them

The script can download:
* Ufora course content
* Ufora notifications
* Opencast paella lecture recordings
* Zoom lecture recordings

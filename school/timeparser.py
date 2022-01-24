from datetime import datetime

from dateutil import tz


def parse(time, fmt=None, utc=True):
    fmt = fmt or "%Y-%m-%dT%H:%M:%S.%fZ"
    timestamp = (
        datetime.strptime(time, fmt)
        if isinstance(time, str)
        else datetime.fromtimestamp(time)
    )
    """ mtime needs to be saved as gmt time(=utc)
    if utc and not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=tz.tzutc())
    timestamp = timestamp.astimezone(tz.tzlocal())"""
    return timestamp.timestamp()


def to_string(timestamp):
    time = datetime.fromtimestamp(timestamp)
    return time.strftime("%d-%m-%Y %H:%M")

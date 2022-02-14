from datetime import datetime


def parse(time, fmt=None, utc=True):
    fmt = fmt or "%Y-%m-%dT%H:%M:%S.%fZ"
    timestamp = (
        datetime.strptime(time, fmt)
        if isinstance(time, str)
        else datetime.fromtimestamp(time)
    )
    return timestamp.timestamp()


def to_string(timestamp):
    time = datetime.fromtimestamp(timestamp)
    return time.strftime("%d-%m-%Y %H:%M")

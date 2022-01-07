from datetime import datetime
from dateutil import tz


def parse(time, fmt=None, utc=True):
    timestamp = datetime.strptime(time, fmt) if isinstance(time, str) else datetime.from_timestamp(time)
    if utc and not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=tz.tzutc())
    timestamp = timestamp.astimezone(tz.tzlocal())
    return timestamp.timestamp()

        
def to_string(timestamp):
    time = datetime.fromtimestamp(timestamp)
    return time.strftime("%d-%m-%Y %H:%M")

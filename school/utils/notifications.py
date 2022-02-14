import json
from datetime import datetime

from school.clients.session import session

from . import constants
from .path import Path


def check_notifications():
    last_announ_seen = Path.content_path("notifications", "notifications").text

    if not last_announ_seen:
        now = datetime.now()
        last_announ_seen = to_string(now.replace(year=now.year - 1))

    new_announ_url = (
        f"https://ufora.ugent.be/d2l/api/lp/1.30/feed/?since={last_announ_seen}"
    )

    content = session.get(new_announ_url).content
    changed = content != b"[]"

    if changed:
        if constants.update_content:
            Path.content_path("notifications", "notifications").text = to_string(
                datetime.now()
            )
        last_announ = json.loads(content)[0]["Metadata"]["Date"]
        changed = last_announ_seen < last_announ

    return changed


def to_string(time):
    return str(time).replace(" ", "T")[:-3] + "Z"

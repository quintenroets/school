import json
from dataclasses import asdict, dataclass

import dacite


@dataclass
class Item:
    @classmethod
    def from_dict(cls, data):
        if isinstance(data, list):
            data = {"items": data}
        return dacite.from_dict(cls, data, config=dacite.Config(strict=True))

    @classmethod
    def from_bytes(cls, data):
        return cls.from_dict(json.loads(data)) if data else cls()

    def dict(self):
        return asdict(self)

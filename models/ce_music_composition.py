"""Trompa AudioObject model
"""

from dataclasses import dataclass
from . import CE_BaseModel, CreativeWork

@dataclass
class CE_MusicComposition(CE_BaseModel, CreativeWork):
    """
    Trompa AudioObject model

    Inherits from schema.org AudioObject
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.format = "text/html"


    def as_dict(self):
        d = {"title": self.title,
             "name": self.name,
             "creator": self.creator,
             "contributor": self.contributor,
             "format_": self.format,
             "source": self.source,
             "subject": self.name,
             "language": self.language,
             }
        if self.identifier is not None:
            d['identifier'] = self.identifier
        return d
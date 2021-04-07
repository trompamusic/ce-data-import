"""Trompa MusicRecording model
"""

from dataclasses import dataclass

from . import CE_BaseModel, CreativeWork


@dataclass
class CE_MusicRecording(CE_BaseModel, CreativeWork):
    """
    Trompa MusicRecording model

    Inherits from schema.org MusicRecording
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.format = "text/html"

    def as_dict(self):
        d = {"title": self.title,
             "name": self.name,
             "creator": self.creator,
             "contributor": self.contributor,
             "encodingformat": self.format,
             "format_": self.format,
             "source": self.source,
             "subject": self.name,
             "description": self.description,
             }
        if self.identifier is not None:
            d['identifier'] = self.identifier
        return d

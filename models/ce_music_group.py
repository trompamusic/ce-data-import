"""Trompa MusicGroup model
"""

from dataclasses import dataclass

from . import CE_BaseModel, MusicGroup


@dataclass
class CE_MusicGroup(MusicGroup, CE_BaseModel):
    """
    Trompa MusicGroup model

    Inherits from schema.org MusicGroup
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str, title: str, source: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.title = title
        self.source = source

    def as_dict(self):
        d = {"title": self.title,
             "contributor": self.contributor,
             "creator": self.creator,
             "format_": self.format,
             "language": self.language,
             "name": self.name,
             "founding_date": self.foundingDate,
             "disolution_date": self.dissolutionDate,
             "description": self.description,
             "image": self.image,
             "publisher": self.publisher,
             "source": self.source,
             }
        if self.identifier is not None:
            d['identifier'] = self.identifier
        return d

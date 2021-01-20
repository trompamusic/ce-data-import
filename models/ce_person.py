"""Trompa Person model
"""

from dataclasses import dataclass
from . import CE_BaseModel, Person

@dataclass
class CE_Person(Person, CE_BaseModel):
    """
    Trompa Person model

    Inherits from schema.org Person
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str, title: str, source: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.title = title
        self.source = source


"""Trompa Person model
"""

from dataclasses import dataclass
from typing import Optional

from . import CE_BaseModel, Person


@dataclass
class CE_Person(Person, CE_BaseModel):
    """
    Trompa Person model

    Inherits from schema.org Person
    """

    def __init__(self, identifier: Optional[str], name: str, url: str, contributor: str, creator: str, title: str, source: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.title = title
        self.source = source

    def as_dict(self):
        d = {"title": self.title,
             "contributor": self.contributor,
             "creator": self.creator,
             "format_": self.format,
             "name": self.name,
             "family_name": self.familyName,
             "given_name": self.givenName,
             "description": self.description,
             "image": self.image,
             "publisher": self.publisher,
             "honorific_prefix": self.honorificPrefix,
             "honorific_suffix": self.honorificSuffix,
             "gender": self.gender,
             "job_title": self.jobTitle,
             "language": self.language,
             "birth_date": self.birthDate,
             "death_date": self.deathDate,
             "source": self.source,
             }
        if self.identifier is not None:
            d['identifier'] = self.identifier
        return d

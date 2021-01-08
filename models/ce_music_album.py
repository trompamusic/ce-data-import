"""Trompa MusicAlbum model
"""

from dataclasses import dataclass
from . import CE_BaseModel, MusicAlbum

@dataclass
class CE_MusicAlbum(MusicAlbum, CE_BaseModel):
    """
    Trompa MusicAlbum model

    Inherits from schema.org MusicAlbum
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)

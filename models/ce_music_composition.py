"""Trompa AudioObject model
"""

from dataclasses import dataclass
from . import CE_BaseModel, MusicRecording

@dataclass
class CE_MusicComposition(CE_BaseModel, MusicRecording):
    """
    Trompa AudioObject model

    Inherits from schema.org AudioObject
    """

    def __init__(self, identifier: str, name: str, url: str, contributor: str, creator: str):
        CE_BaseModel.__init__(self, identifier, name, url, contributor, creator)
        self.format = "text/html"

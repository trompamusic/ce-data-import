"""
Data models as described by the Trompa CE and Schema.org definitions.
"""
from .sdo_thing import Thing
from .sdo_organization import Organization
from .sdo_person import Person
from .sdo_place import Place
from .sdo_creative_work import CreativeWork
from .sdo_media_object import MediaObject
from .sdo_audio_object import AudioObject
from .sdo_music_recording import MusicRecording
from .sdo_music_playlist import MusicPlaylist
from .sdo_music_album import MusicAlbum

from .ce_base import CE_BaseModel
from .ce_audio_object import CE_AudioObject
from .ce_music_album import CE_MusicAlbum
from .ce_person import CE_Person

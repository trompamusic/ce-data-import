"""
Import per data type
"""
from .artist import import_artist
from .music_album import import_album
from .audio_object import import_tracks
from .musicbrainz import load_person_from_musicbrainz
from .isni import load_person_from_isni
from .viaf import load_person_from_viaf
from .wikidata import load_person_from_wikidata
from .wikidata import load_person_from_wikipedia
from .ceimport import cache

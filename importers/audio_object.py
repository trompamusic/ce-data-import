"""
Muziekweb music fragment importer
"""
import json
import trompace as ce

from datetime import datetime, date
from trompace.connection import submit_query
from trompace.mutations.mediaobject import mutation_update_media_object, mutation_create_media_object
from trompace_local import GLOBAL_CONTRIBUTOR, GLOBAL_IMPORTER_REPO, GLOBAL_PUBLISHER, lookupIdentifier

from models import CE_AudioObject
from muziekweb_api import get_album_information

MW_AUDIO_URL = "https://www.muziekweb.nl/Embed/{}"


async def import_tracks(key: str):
    """
    Imports audio fragments from Muziekweb for the key into the Trompa CE.
    """
    print(f"Retrieving release info with key {key} from Muziekweb")
    # Get data from Muziekweb
    tracks = get_mw_audio(key)

    if tracks is None:
        print(f"No track data received for {key}")
        return

    # Loop the tracks on the release to add all references to the 30 seconds music fragment
    for track in tracks:

        track.identifier = await lookupIdentifier("AudioObject", track.source)

        if track.identifier is not None:
            print(f"Updating record {track.identifier} in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_update_media_object(
                identifier=track.identifier,
                title=track.name,
                description=track.description,
                date=date.today(),
                creator=track.creator,
                contributor=track.contributor,
                format_=track.format,
                encodingFormat=track.format,
                source=track.source,
                subject=track.name,
                contentUrl=track.contentUrl,
                language=track.language
            ))
            track.identifier = response["data"]["UpdatePerson"]["identifier"]
        else:
            print("Inserting new record in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_create_media_object(
                name=track.name,
                title=track.name,
                description=track.description,
                date=date.today(),
                creator=track.creator,
                contributor=track.contributor,
                format_=track.format,
                encodingFormat=track.format,
                source=track.source,
                subject=track.name,
                contentUrl=track.contentUrl,
                language=track.language
            ))
            track.identifier = response["data"]["CreatePerson"]["identifier"]

    print(f"Importing tracks for {key} done.")


def get_mw_audio(key: str) -> [CE_AudioObject]:
    # Use the Muziekweb API to retrieve all the tracks on the album
    doc = get_album_information(key)

    if doc is not None and doc.firstChild.tagName == "Result" and doc.firstChild.attributes['ErrorCode'].value == "0":

        # Now extract the audio links from the Muziekweb data
        audio_objects = list()

        for track in doc.getElementsByTagName('Track'):

            trackId = track.getElementsByTagName('AlbumTrackID')[0].firstChild.data

            audio_object = CE_AudioObject(
                identifier = None,
                name = trackId,
                url = MW_AUDIO_URL.format(trackId),
                contributor = GLOBAL_CONTRIBUTOR,
                creator = GLOBAL_IMPORTER_REPO,
            )

            audio_object.title = track.getElementsByTagName('TrackTitle')[0].firstChild.data,
            audio_object.publisher = GLOBAL_PUBLISHER
            audio_object.description = 'Embed in frame using the following code: <iframe width="300" height="30" src="[url]" frameborder="no" scrolling="no" allowtransparency="true"></iframe>'

            audio_objects.append(audio_object)

        return audio_objects

    return None

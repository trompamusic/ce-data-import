"""
Muziekweb album importer
"""
import json
import trompace as ce

from datetime import datetime, date
from SPARQLWrapper import SPARQLWrapper, JSON
from trompace.connection import submit_query
#from trompace.mutations.music_album import mutation_update_music_album, mutation_create_music_album
from trompace_local import GLOBAL_CONTRIBUTOR, GLOBAL_IMPORTER_REPO, GLOBAL_PUBLISHER, lookupIdentifier
from models import CE_MusicAlbum
from .audio_object import import_tracks

async def import_album(keys: list):
    """
    Imports albums from Muziekweb for all given keys into the Trompa CE.
    """
    for key in keys:
        '''
        #Not yet available in Trompa ce-client
        print(f"Retrieving album with key {key} from Muziekweb")
        # Get data from Muziekweb
        album = await get_mw_album(key)

        if album is None:
            print(f"No data received for {key}")
            continue

        album.identifier = await lookupIdentifier("MusicAlbum", album.source)

        if album.identifier is not None:
            print(f"Updating record {album.identifier} in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_update_music_album(
                identifier=album.identifier,
                name=album.name,
                publisher=album.publisher,
                contributor=album.contributor,
                creator=album.creator,
                source=album.source,
                description=album.description,
                language=album.language,
                coverage=None,
                #formatin="text/html",
                date=date.today(),
                disambiguatingDescription=album.disambiguatingDescription,
                relation=album.relatedTo,
                _type=None,
                _searchScore=None
            ))
            album.identifier = response["data"]["UpdateMusicAlbum"]["identifier"]
        else:
            print("Inserting new record in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_create_music_album(
                artist_name=album.name,
                publisher=album.publisher,
                contributor=album.contributor,
                creator=album.creator,
                source=album.source,
                description=album.description,
                language=album.language,
                coverage=None,
                #formatin="text/html",
                date=date.today(),
                disambiguatingDescription=album.disambiguatingDescription,
                relation=album.relatedTo,
                _type=None,
                _searchScore=None,
            ))
            album.identifier = response["data"]["MusicAlbum"]["identifier"]

        if album.identifier is None:
            print(" - failed.")
        else:
            print(" - success.")
        '''

        # Now import the audio fragments
        await import_tracks(key)

    print("Importing albums done.")


async def get_mw_album(key: str) -> CE_MusicAlbum:
    sparql = SPARQLWrapper("https://api.data.muziekweb.nl/datasets/muziekweborganization/Muziekweb/services/Muziekweb/sparql")
    sparql.setReturnFormat(JSON)
    qry = f"""PREFIX schema: <http://schema.org/>
    PREFIX vocab: <https://data.muziekweb.nl/vocab/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?url ?title ?published where {{
        BIND(<https://data.muziekweb.nl/Link/{key}> as ?url)
        ?url schema:datePublished ?published;
        rdfs:label ?title.
    }}"""
    sparql.setQuery(qry)

    result = sparql.query().convert()["results"]["bindings"]

    if len(result) > 0:
        # Now get Muziekweb data
        album = CE_MusicAlbum(
            identifier = None,
            name = result[0]["title"]["value"],
            url = result[0]["url"]["value"],
            contributor = GLOBAL_CONTRIBUTOR,
            creator = GLOBAL_IMPORTER_REPO,
        )

        album.publisher = GLOBAL_PUBLISHER
        album.description = None
        album.datePublished = result[0]["published"]["value"]

        return album

    return None

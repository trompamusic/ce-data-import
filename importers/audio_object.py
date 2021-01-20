"""
Muziekweb music fragment importer
"""
import json
import trompace as ce

from datetime import datetime, date
from trompace.connection import submit_query
from trompace.mutations.audioobject import mutation_update_audio_object, mutation_create_audio_object, mutation_merge_audio_object_work_example
from trompace.mutations.musiccomposition import mutation_update_music_composition, mutation_create_music_composition, mutation_merge_music_composition_composer
from trompace.mutations.person import mutation_update_person, mutation_create_person, mutation_person_add_exact_match_person
from trompace_local import GLOBAL_CONTRIBUTOR, GLOBAL_IMPORTER_REPO, GLOBAL_PUBLISHER, lookupIdentifier

from models import CE_AudioObject, CE_Person, CE_MusicComposition
from muziekweb_api import get_album_information, get_track_information, get_artist_information
from importers.isni import load_person_from_isni
from importers.musicbrainz import load_person_from_musicbrainz
from importers.viaf import load_person_from_viaf
from importers.wikidata import load_person_from_wikidata, load_person_from_wikipedia
import itertools

MW_AUDIO_URL = "https://www.muziekweb.nl/Embed/{}"
MW_MUSIC_URL = "https://www.muziekweb.nl/en/Link/{}/{}/{}"

import pdb

async def import_tracks(key: str):
    """
    Imports audio fragments from Muziekweb for the key into the Trompa CE.
    """
    print(f"Retrieving release info with key {key} from Muziekweb")
    # Get data from Muziekweb
    tracks, music_works, persons = get_mw_audio_1track(key)
    # tracks = get_mw_audio(key)

    if tracks is None or len(tracks) == 0:
        print(f"No track data received for {key}")
        return

    #####################################
    # PERSONS
    # Loop the persons on all external links to add references for each CE_person
    #####################################
    list_person_ids = list()
    for person in persons:

        person.identifier = await lookupIdentifier("Person", person.source)
        
        if person.identifier is not None:
            print(f"Updating person {person.identifier} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_update_person(
                identifier=person.identifier,
                title=person.title,
                contributor=person.contributor,
                creator=person.creator,
                format_=person.format,
                name=person.name,
                family_name=person.familyName,
                given_name=person.givenName,
                description=person.description,
                image=person.image,
                publisher=person.publisher,
                honorific_prefix=person.honorificPrefix,
                honorific_suffix=person.honorificSuffix,
                gender=person.gender,
                job_title=person.jobTitle,
                language=person.language,
                birth_date=person.birthDate,
                death_date=person.deathDate,
                source=person.source,
            ))
            person.identifier = response["data"]["UpdatePerson"]["identifier"]
            list_person_ids.append(person.identifier)
        else:
            print("Inserting new person {person.name} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_create_person(
                title=person.title,
                contributor=person.contributor,
                creator=person.creator,
                format_=person.format,
                name=person.name,
                family_name=person.familyName,
                given_name=person.givenName,
                description=person.description,
                image=person.image,
                publisher=person.publisher,
                honorific_prefix=person.honorificPrefix,
                honorific_suffix=person.honorificSuffix,
                gender=person.gender,
                job_title=person.jobTitle,
                language=person.language,
                birth_date=person.birthDate,
                death_date=person.deathDate,
                source=person.source,
            ))

            person.identifier = response["data"]["CreatePerson"]["identifier"]
            list_person_ids.append(person.identifier)

    print(f"Importing Persons for {key} done.")

    #####################################
    # Linking PERSONS
    # Loop the person identifiers and link them 
    #####################################
    for from_id, to_id in itertools.permutations(list_person_ids, 2):
        query = mutation_person_add_exact_match_person(from_id, to_id)
        response = await ce.connection.submit_query_async(query)
        print(f"   - Linking Person {from_id} to Person {to_id} done.")

    #####################################
    # MUSICCOMPOSITION
    # Loop the music works to create the CE_MusicComposition on the CE
    #####################################
    for work in music_works:

        work.identifier = await lookupIdentifier("MusicComposition", work.source)
        # print(track)
        
        if work.identifier is not None:
            print(f"Updating work {work.identifier} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_update_music_composition(
                identifier=work.identifier,
                title=work.title,
                name=work.name,
                creator=work.creator,
                contributor=work.contributor,
                format_=work.format,
                source=work.source,
                subject=work.name,
                language=work.language,
            ))
            work.identifier = response["data"]["UpdateMusicComposition"]["identifier"]
        else:
            print("Inserting new work {work.name} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_create_music_composition(
                title=work.title,
                name=work.name,
                creator=work.creator,
                contributor=work.contributor,
                format_=work.format,
                source=work.source,
                subject=work.name,
                language=work.language,
            ))

            work.identifier = response["data"]["CreateMusicComposition"]["identifier"]

    print(f"Importing music composition {work.identifier} done.\n")

    #####################################
    # Linking PERSONS and MUSICCOMPOSITIONS
    # Loop the person identifiers and link them to music compositions
    #####################################
    for person_id in list_person_ids:
        query = mutation_merge_music_composition_composer(work.identifier, person_id)
        response = await ce.connection.submit_query_async(query)
        print(f"   - Linking Person {person_id} to MusicComposition {work.identifier} done.\n")


    #####################################
    # AUDIOOBJECTS
    # Loop the tracks to create the CE_AudioObject on the CE
    #####################################
    for track in tracks:

        track.identifier = await lookupIdentifier("AudioObject", track.source)
        # print(track)
        
        if track.identifier is not None:
            print(f"Updating record {track.identifier} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_update_audio_object(
                identifier=track.identifier,
                title=track.title,
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
            track.identifier = response["data"]["UpdateAudioObject"]["identifier"]
        else:
            print("Inserting new track {track.title} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_create_audio_object(
                name=track.name,
                title=track.title,
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

            track.identifier = response["data"]["CreateAudioObject"]["identifier"]

    print(f"Importing tracks {track.identifier} done.\n")

    #####################################
    # Linking MUSICCOMPOSITIONS and AUDIOOBJECTS
    # Loop the musicworks identifiers and link them to audioobjects
    #####################################
    query = mutation_merge_audio_object_work_example(track.identifier, work.identifier)
    response = await ce.connection.submit_query_async(query)
    print(f"   - Linking MusicComposition {work.identifier} to AudioObject {track.identifier} done.")


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

            audio_object.title = track.getElementsByTagName('TrackTitle')[0].firstChild.data
            audio_object.publisher = GLOBAL_PUBLISHER
            audio_object.description = 'Embed in frame using the following code: <iframe width="300" height="30" src="[url]" frameborder="no" scrolling="no" allowtransparency="true"></iframe>'

            audio_objects.append(audio_object)

        return audio_objects

    return None

def get_mw_audio_1track(key: str) -> [CE_AudioObject]:
    # Use the Muziekweb API to retrieve one track

    key_album = key.split('-')[0]

    doc = get_album_information(key_album)

    if doc is not None and doc.firstChild.tagName == "Result" and doc.firstChild.attributes['ErrorCode'].value == "0":

        # Now extract the audio links from the Muziekweb data
        audio_objects = list()
        music_works = list()
        persons = list()

        for track in doc.getElementsByTagName('Track'):

            trackId = track.getElementsByTagName('AlbumTrackID')[0].firstChild.data

            if trackId == key:
                # append audio object
                audio_object = CE_AudioObject(
                    identifier = None,
                    name = track.getElementsByTagName('TrackTitle')[0].firstChild.data,
                    url = MW_AUDIO_URL.format(trackId),
                    contributor = GLOBAL_CONTRIBUTOR,
                    creator = GLOBAL_IMPORTER_REPO,
                )
                
                audio_object.title = "Muziekweb - de muziekbibliotheek van Nederland"
                audio_object.publisher = GLOBAL_PUBLISHER
                audio_object.description = 'Embed in frame using the following code: <iframe width="300" height="30" src="[url]" frameborder="no" scrolling="no" allowtransparency="true"></iframe>'

                audio_objects.append(audio_object)
                # print(audio_objects)

                # append musicwork
                unif_title = track.getElementsByTagName('UniformTitle')[0].attributes['Link'].value
                unif_text = track.getElementsByTagName('UniformTitle')[0].firstChild.data.replace(' ', '-')
                unif_style = track.getElementsByTagName('Catalogue')[0].firstChild.data.split(' ')[0]
                # print(MW_MUSIC_URL.format(unif_title, unif_style, unif_text))
                
                music_work = CE_MusicComposition(
                    identifier = None,
                    name = track.getElementsByTagName('TrackTitle')[0].firstChild.data,
                    url = MW_MUSIC_URL.format(unif_title, unif_style, unif_text),
                    contributor = GLOBAL_CONTRIBUTOR,
                    creator = GLOBAL_IMPORTER_REPO,
                )

                music_work.title = 'Muziekweb - de muziekbibliotheek van Nederland'
                music_work.contributor = GLOBAL_CONTRIBUTOR
                music_work.source = MW_MUSIC_URL.format(unif_title, unif_style, unif_text)

                music_works.append(music_work)
                # print(music_works)
                # append persons
                perf_link = track.getElementsByTagName('Performer')[0].attributes['Link'].value
                doc_artist = get_artist_information(perf_link)
                num_persons = int(doc_artist.getElementsByTagName('ExternalLinks')[0].attributes['Count'].value) 
                perf_name = doc_artist.getElementsByTagName('PresentationName')[0].firstChild.data
                perf_text = perf_name.replace(' ', '-')

                #MW person
                person = CE_Person(
                    identifier = None,
                    name = '{} - Muziekweb'.format(perf_name),
                    url = MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
                    contributor = GLOBAL_CONTRIBUTOR,
                    creator = GLOBAL_IMPORTER_REPO, 
                    title = '{} - Muziekweb'.format(perf_name),
                    source = MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
                )
                persons.append(person)

                # external links
                for pers in range(num_persons):
                    
                    prov_name = doc_artist.getElementsByTagName('ExternalLink')[pers].attributes['Provider'].value
                    print('Searching for person: {} - {}'.format(perf_name, prov_name))
                    ext_link = doc_artist.getElementsByTagName('ExternalLinks')[0].getElementsByTagName('Link')[pers].firstChild.data
                    if prov_name == 'ISNI':
                        ext_link = MW_MUSIC_URL.format(perf_link, unif_style, ext_link)
                        ppl = load_person_from_isni(ext_link)
                        person = CE_Person(
                            identifier = None,
                            name = ppl['title'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                    elif prov_name == 'VIAF':
                        ppl = load_person_from_viaf(ext_link)
                        person = CE_Person(
                            identifier = None,
                            name = ppl['title'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                    elif prov_name == 'MUSICBRAINZ':
                        mbid = ext_link.split('/')[-1]
                        ppl = load_person_from_musicbrainz(mbid)
                        person = CE_Person(
                            identifier = None,
                            name = ppl['title'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                        person.birthPlace = ppl['birthplace']
                        person.birthDate = ppl['birth_date']
                        person.deathPlace = ppl['deathplace']
                        person.deathDate = ppl['death_date']
                    elif prov_name == 'WIKIDATA':
                        ppl = load_person_from_wikidata(ext_link)
                        wiki_data_link = ext_link
                        person = CE_Person(
                            identifier = None,
                            name = ppl['title'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                        person.description = ppl['description']
                    elif prov_name == 'WIKIPEDIA_EN':
                        ext_link = 'https://en.wikipedia.org/wiki/{}'.format(ext_link)
                        ppl = load_person_from_wikipedia(wiki_data_link, 'en')
                        person = CE_Person(
                            identifier = None,
                            name = ppl['name'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                        person.description = ppl['description']

                    elif prov_name == 'WIKIPEDIA_NL':
                        ext_link = 'https://nl.wikipedia.org/wiki/{}'.format(ext_link)
                        ppl = load_person_from_wikipedia(wiki_data_link, 'nl')
                        person = CE_Person(
                            identifier = None,
                            name = ppl['name'],
                            url = ppl['source'],
                            contributor = ppl['contributor'],
                            creator = GLOBAL_IMPORTER_REPO,
                            title = ppl['title'],
                            source = ppl['source'],
                        )
                        person.description = ppl['description']
                    else:
                        if prov_name == 'ALLMUSIC':
                            contributor = 'https://www.allmusic.com/'
                        elif prov_name == 'DISCOGS':
                            contributor = 'https://www.discogs.com/'
                        elif prov_name == 'LASTFM':
                            contributor = 'https://www.last.fm/'

                        person = CE_Person(
                            identifier = None,
                            name = '{} - {}'.format(perf_name, prov_name),
                            url = ext_link,
                            contributor = contributor,
                            creator = GLOBAL_IMPORTER_REPO,
                            title = '{} - {}'.format(perf_name, prov_name),
                            source = ext_link,
                        )
                    persons.append(person)
                    print('External link: {}'.format(ext_link))


        return audio_objects, music_works, persons

    return None
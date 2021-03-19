"""
Muziekweb music fragment importer
"""
import itertools

import trompace as ce
from trompace.connection import submit_query
from trompace.mutations.audioobject import mutation_update_audioobject, mutation_create_audioobject, \
    mutation_merge_audioobject_exampleofwork
from trompace.mutations.musiccomposition import mutation_update_music_composition, mutation_create_music_composition, \
    mutation_merge_music_composition_composer
from trompace.mutations.person import mutation_update_person, mutation_create_person, \
    mutation_person_add_exact_match_person
from trompace.mutations.musicgroup import mutation_create_musicgroup, \
    mutation_update_musicgroup, mutation_delete_musicgroup, \
    mutation_musicgroup_add_exact_match_musicgroup, mutation_add_musicgroup_member

from ceimport.sites.isni import load_person_from_isni
# from ceimport.sites.musicbrainz import load_person_data_from_musicbrainz
from ceimport.sites import musicbrainz
from ceimport.sites.viaf import load_person_from_viaf
from ceimport.sites.wikidata import load_person_from_wikidata_url, load_person_from_wikipedia_url
from models import CE_AudioObject, CE_Person, CE_MusicComposition, CE_MusicGroup
from muziekweb_api import get_album_information, get_artist_information
from trompace_local import GLOBAL_CONTRIBUTOR, GLOBAL_IMPORTER_REPO, GLOBAL_PUBLISHER, lookupIdentifier

MW_AUDIO_URL = "https://www.muziekweb.nl/Embed/{}"
MW_MUSIC_URL = "https://www.muziekweb.nl/en/Link/{}/{}/{}"


async def import_tracks(key: str):
    """
    Imports audio fragments from Muziekweb for the key into the Trompa CE.
    """
    print(f"Retrieving release info with key {key} from Muziekweb")
    # Get data from Muziekweb
    tracks, music_works, persons, music_groups = get_mw_audio_1track(key)
    # tracks = get_mw_audio(key)

    if tracks is None or len(tracks) == 0:
        print(f"No track data received for {key}")
        return

    #####################################
    # MUSICCOMPOSITION
    # Loop the music works to create the CE_MusicComposition on the CE
    #####################################
    for work in music_works:

        work.identifier = await lookupIdentifier("MusicComposition", work.source)

        if work.identifier is not None:
            print(f"Updating work {work.identifier} in Trompa CE\n", end="")

            response = await ce.connection.submit_query_async(mutation_update_music_composition(**work.as_dict()))
            work.identifier = response["data"]["UpdateMusicComposition"]["identifier"]
        else:
            print("Inserting new work {} in Trompa CE\n".format(work.name))

            response = await ce.connection.submit_query_async(mutation_create_music_composition(**work.as_dict()))
            work.identifier = response["data"]["CreateMusicComposition"]["identifier"]

    print(f"Importing music composition {work.identifier} done.\n")

    #####################################
    # PERSONS
    # Loop the persons on all external links to add references for each CE_person
    #####################################
    list_person_ids = list()
    for person in persons:

        person.identifier = await lookupIdentifier("Person", person.source)

        if person.identifier is not None:
            print(f"Updating person {person.identifier} in Trompa CE\n")

            response = await ce.connection.submit_query_async(mutation_update_person(**person.as_dict()))
            person.identifier = response["data"]["UpdatePerson"]["identifier"]
            list_person_ids.append(person.identifier)
        else:
            print("Inserting new person {} in Trompa CE\n".format(person.name))

            response = await ce.connection.submit_query_async(mutation_create_person(**person.as_dict()))

            person.identifier = response["data"]["CreatePerson"]["identifier"]
            list_person_ids.append(person.identifier)

    if list_person_ids:
        print(f"Importing Persons for {key} done.")

    #####################################
    # Linking PERSONS
    # Loop the person identifiers and link them
    #####################################
    if not music_groups:
        for from_id, to_id in itertools.permutations(list_person_ids, 2):
            query = mutation_person_add_exact_match_person(from_id, to_id)
            response = await ce.connection.submit_query_async(query)
            print(f"   - Linking Person {from_id} to Person {to_id} done.")

    #####################################
    # Linking PERSONS and MUSICCOMPOSITIONS
    # Loop the person identifiers and link them to music compositions
    #####################################
    for person_id in list_person_ids:
        query = mutation_merge_music_composition_composer(work.identifier, person_id)
        response = await ce.connection.submit_query_async(query)
        print(f"   - Linking Person {person_id} to MusicComposition {work.identifier} done.\n")

    #####################################
    # MUSIC GROUPS
    # Loop the Music Groups on all external links to add references for each CE_person
    #####################################
    list_music_group_ids = list()
    for music_group in music_groups:

        music_group.identifier = await lookupIdentifier("MusicGroup", music_group.source)

        if music_group.identifier is not None:
            print(f"Updating music group {music_group.identifier} in Trompa CE\n")

            response = await ce.connection.submit_query_async(mutation_update_musicgroup(**music_group.as_dict()))
            music_group.identifier = response["data"]["UpdateMusicGroup"]["identifier"]
            list_music_group_ids.append(music_group.identifier)
        else:
            print("Inserting new music group {} in Trompa CE\n".format(music_group.name))

            response = await ce.connection.submit_query_async(mutation_create_musicgroup(**music_group.as_dict()))

            music_group.identifier = response["data"]["CreateMusicGroup"]["identifier"]
            list_music_group_ids.append(music_group.identifier)

    if list_music_group_ids:
        print(f"Importing Music Groups for {key} done.")

    #####################################
    # Linking MUSIC GROUPS
    # Loop the music groups identifiers and link them
    #####################################
    for from_id, to_id in itertools.permutations(list_music_group_ids, 2):
        query = mutation_musicgroup_add_exact_match_musicgroup(from_id, to_id)
        response = await ce.connection.submit_query_async(query)
        print(f"   - Linking Music Group {from_id} to Music Group {to_id} done.")

    #####################################
    # Linking MUSIC GROUPS and MUSICCOMPOSITIONS
    # Loop the music group identifiers and link them to music compositions
    #####################################
    for music_group_id in list_music_group_ids:
        query = mutation_merge_music_composition_composer(work.identifier, music_group_id)
        response = await ce.connection.submit_query_async(query)
        print(f"   - Linking MusicGroup {music_group_id} to MusicComposition {work.identifier} done.\n")

    #####################################
    # Linking MUSIC GROUPS and PERSONS
    # Loop the music group identifiers and link them to person identifiers
    #####################################
    for music_group_id in list_music_group_ids:
        for person_id in list_person_ids:
            query = mutation_add_musicgroup_member(person_id, music_group_id)
            response = await ce.connection.submit_query_async(query)
            print(f"   - Linking Person {person_id} to MusicGroup {music_group_id} done.\n")

    #####################################
    # AUDIOOBJECTS
    # Loop the tracks to create the CE_AudioObject on the CE
    #####################################
    for track in tracks:

        track.identifier = await lookupIdentifier("AudioObject", track.source)

        if track.identifier is not None:
            print(f"Updating record {track.identifier} in Trompa CE\n")

            response = await ce.connection.submit_query_async(mutation_update_audioobject(**track.as_dict()))
            track.identifier = response["data"]["UpdateAudioObject"]["identifier"]
        else:
            print("Inserting new track {} in Trompa CE\n".format(track.title))

            response = await ce.connection.submit_query_async(mutation_create_audioobject(**track.as_dict()))
            track.identifier = response["data"]["CreateAudioObject"]["identifier"]

    print(f"Importing tracks {track.identifier} done.\n")

    #####################################
    # Linking MUSICCOMPOSITIONS and AUDIOOBJECTS
    # Loop the musicworks identifiers and link them to audioobjects
    #####################################
    query = mutation_merge_audioobject_exampleofwork(track.identifier, work.identifier)
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
                identifier=None,
                name=trackId,
                url=MW_AUDIO_URL.format(trackId),
                contributor=GLOBAL_CONTRIBUTOR,
                creator=GLOBAL_IMPORTER_REPO,
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
        music_groups = list()

        for track in doc.getElementsByTagName('Track'):

            trackId = track.getElementsByTagName('AlbumTrackID')[0].firstChild.data

            if trackId == key:
                # append audio object
                audio_object = CE_AudioObject(
                    identifier=None,
                    name=track.getElementsByTagName('TrackTitle')[0].firstChild.data,
                    url=MW_AUDIO_URL.format(trackId),
                    contributor=GLOBAL_CONTRIBUTOR,
                    creator=GLOBAL_IMPORTER_REPO,
                )

                audio_object.title = "Muziekweb - de muziekbibliotheek van Nederland"
                audio_object.publisher = GLOBAL_PUBLISHER
                audio_object.description = 'Embed in frame using the following code: <iframe width="300" height="30" src="[url]" frameborder="no" scrolling="no" allowtransparency="true"></iframe>'

                audio_objects.append(audio_object)

                # append musicwork
                unif_title = track.getElementsByTagName('UniformTitle')[0].attributes['Link'].value
                unif_text = track.getElementsByTagName('UniformTitle')[0].firstChild.data.replace(' ', '-')
                unif_style = track.getElementsByTagName('Catalogue')[0].firstChild.data.split(' ')[0]

                music_work = CE_MusicComposition(
                    identifier=None,
                    name=track.getElementsByTagName('TrackTitle')[0].firstChild.data,
                    url=MW_MUSIC_URL.format(unif_title, unif_style, unif_text),
                    contributor=GLOBAL_CONTRIBUTOR,
                    creator=GLOBAL_IMPORTER_REPO,
                )

                music_work.title = 'Muziekweb - de muziekbibliotheek van Nederland'
                music_work.contributor = GLOBAL_CONTRIBUTOR
                music_work.source = MW_MUSIC_URL.format(unif_title, unif_style, unif_text)
                music_works.append(music_work)
                # append persons
                perf_link = track.getElementsByTagName('Performer')[0].attributes['Link'].value
                doc_artist = get_artist_information(perf_link)
                num_ext_links = int(doc_artist.getElementsByTagName('ExternalLinks')[0].attributes['Count'].value)
                perf_name = doc_artist.getElementsByTagName('PresentationName')[0].firstChild.data
                perf_text = perf_name.replace(' ', '-')
                # check if person or musicgroup
                prov_names = [doc_artist.getElementsByTagName('ExternalLink')[pers].attributes['Provider'].value for pers in range(num_ext_links)]
                artist_type = None
                if 'MUSICBRAINZ' in prov_names:
                    ext_link = doc_artist.getElementsByTagName('ExternalLinks')[0].getElementsByTagName('Link')[prov_names.index('MUSICBRAINZ')].firstChild.data
                    mbid = ext_link.split('/')[-1]
                    artist = musicbrainz.get_artist_from_musicbrainz(mbid)
                    artist_type = artist['type']

                if artist_type == 'Person' or not artist_type:
                    persons = get_person_information(doc_artist, persons, num_ext_links, perf_name, perf_link, perf_text, unif_style)
                elif artist_type == 'Group':
                    music_groups, persons = get_music_group_information(doc_artist, music_groups, persons, num_ext_links, perf_name, perf_link, perf_text, unif_style)

        return audio_objects, music_works, persons, music_groups

    return None


def get_person_information(doc_artist, persons, num_ext_links, perf_name, perf_link, perf_text, unif_style):
    """
    """
    # MW person
    person = CE_Person(
        identifier=None,
        name='{} - Muziekweb'.format(perf_name),
        url=MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
        contributor=GLOBAL_CONTRIBUTOR,
        creator=GLOBAL_IMPORTER_REPO,
        title='{} - Muziekweb'.format(perf_name),
        source=MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
    )
    persons.append(person)

    # external links
    for pers in range(num_ext_links):

        prov_name = doc_artist.getElementsByTagName('ExternalLink')[pers].attributes['Provider'].value
        print('Searching for person: {} - {}'.format(perf_name, prov_name))
        ext_link = doc_artist.getElementsByTagName('ExternalLinks')[0].getElementsByTagName('Link')[
            pers].firstChild.data
        if prov_name == 'ISNI':
            ext_link = MW_MUSIC_URL.format(perf_link, unif_style, ext_link)
            ppl = load_person_from_isni(ext_link)
            person = CE_Person(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
        elif prov_name == 'VIAF':
            ppl = load_person_from_viaf(ext_link)
            person = CE_Person(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
        elif prov_name == 'MUSICBRAINZ':
            mbid = ext_link.split('/')[-1]
            ppls = musicbrainz.load_artist_from_musicbrainz(mbid)
            for ppl in ppls:
                person = CE_Person(
                    identifier=None,
                    name=ppl['title'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                person.birthPlace = ppl['birth_place']
                person.birthDate = ppl['birth_date']
                person.deathPlace = ppl['death_place']
                person.deathDate = ppl['death_date']
                persons.append(person)

        elif prov_name == 'WIKIDATA':
            ppl = load_person_from_wikidata_url(ext_link)
            person = CE_Person(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
            person.description = ppl['description']
        elif prov_name == 'WIKIPEDIA_EN':
            en_wiki_link = 'https://en.wikipedia.org/wiki/{}'.format(ext_link)
            ppl = load_person_from_wikipedia_url(en_wiki_link, 'en')
            if ppl:
                person = CE_Person(
                    identifier=None,
                    name=ppl['name'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                person.description = ppl['description']

        elif prov_name == 'WIKIPEDIA_NL':
            nl_wiki_link = 'https://nl.wikipedia.org/wiki/{}'.format(ext_link)
            ppl = load_person_from_wikipedia_url(nl_wiki_link, 'nl')
            if ppl:
                person = CE_Person(
                    identifier=None,
                    name=ppl['name'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                person.description = ppl['description']
        else:
            if prov_name == 'ALLMUSIC':
                contributor = 'https://www.allmusic.com/'
            elif prov_name == 'DISCOGS':
                contributor = 'https://www.discogs.com/'
            elif prov_name == 'LASTFM':
                contributor = 'https://www.last.fm/'
            else:
                continue

            person = CE_Person(
                identifier=None,
                name='{} - {}'.format(perf_name, prov_name),
                url=ext_link,
                contributor=contributor,
                creator=GLOBAL_IMPORTER_REPO,
                title='{} - {}'.format(perf_name, prov_name),
                source=ext_link,
            )
        persons.append(person)
        print('External link: {}'.format(ext_link))
    return persons


def get_music_group_information(doc_artist, music_groups, persons, num_ext_links, perf_name, perf_link, perf_text, unif_style):
    """
    """
    # MW Music Group
    music_group = CE_MusicGroup(
        identifier=None,
        name='{} - Muziekweb'.format(perf_name),
        url=MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
        contributor=GLOBAL_CONTRIBUTOR,
        creator=GLOBAL_IMPORTER_REPO,
        title='{} - Muziekweb'.format(perf_name),
        source=MW_MUSIC_URL.format(perf_link, unif_style, perf_text),
    )
    music_groups.append(music_group)

    # external links
    for pers in range(num_ext_links):
        prov_name = doc_artist.getElementsByTagName('ExternalLink')[pers].attributes['Provider'].value
        print('Searching for music group: {} - {}'.format(perf_name, prov_name))
        ext_link = doc_artist.getElementsByTagName('ExternalLinks')[0].getElementsByTagName('Link')[
            pers].firstChild.data
        if prov_name == 'ISNI':
            ext_link = MW_MUSIC_URL.format(perf_link, unif_style, ext_link)
            ppl = load_person_from_isni(ext_link)
            music_group = CE_MusicGroup(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
        elif prov_name == 'VIAF':
            ppl = load_person_from_viaf(ext_link)
            music_group = CE_MusicGroup(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
        elif prov_name == 'MUSICBRAINZ':
            mbid = ext_link.split('/')[-1]

            ppls = musicbrainz.load_artist_from_musicbrainz(mbid)

            for ppl in ppls:
                person = CE_Person(
                    identifier=None,
                    name=ppl['title'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                person.birthPlace = ppl['birth_place']
                person.birthDate = ppl['birth_date']
                person.deathPlace = ppl['death_place']
                person.deathDate = ppl['death_date']
                persons.append(person)

        elif prov_name == 'WIKIDATA':
            ppl = load_person_from_wikidata_url(ext_link)
            music_group = CE_MusicGroup(
                identifier=None,
                name=ppl['title'],
                url=ppl['source'],
                contributor=ppl['contributor'],
                creator=GLOBAL_IMPORTER_REPO,
                title=ppl['title'],
                source=ppl['source'],
            )
            music_group.description = ppl['description']
        elif prov_name == 'WIKIPEDIA_EN':
            en_wiki_link = 'https://en.wikipedia.org/wiki/{}'.format(ext_link)
            ppl = load_person_from_wikipedia_url(en_wiki_link, 'en')
            if ppl:
                music_group = CE_MusicGroup(
                    identifier=None,
                    name=ppl['name'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                music_group.description = ppl['description']

        elif prov_name == 'WIKIPEDIA_NL':
            nl_wiki_link = 'https://nl.wikipedia.org/wiki/{}'.format(ext_link)
            ppl = load_person_from_wikipedia_url(nl_wiki_link, 'nl')
            if ppl:
                music_group = CE_MusicGroup(
                    identifier=None,
                    name=ppl['name'],
                    url=ppl['source'],
                    contributor=ppl['contributor'],
                    creator=GLOBAL_IMPORTER_REPO,
                    title=ppl['title'],
                    source=ppl['source'],
                )
                music_group.description = ppl['description']
        else:
            if prov_name == 'ALLMUSIC':
                contributor = 'https://www.allmusic.com/'
            elif prov_name == 'DISCOGS':
                contributor = 'https://www.discogs.com/'
            elif prov_name == 'LASTFM':
                contributor = 'https://www.last.fm/'
            else:
                continue

            music_group = CE_MusicGroup(
                identifier=None,
                name='{} - {}'.format(perf_name, prov_name),
                url=ext_link,
                contributor=contributor,
                creator=GLOBAL_IMPORTER_REPO,
                title='{} - {}'.format(perf_name, prov_name),
                source=ext_link,
            )
        music_groups.append(music_group)
        print('External link: {}'.format(ext_link))

    return music_groups, persons

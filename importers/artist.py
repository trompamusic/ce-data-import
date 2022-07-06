"""
Muziekweb artist importer
"""
import itertools

import trompace.connection
from trompace.mutations.person import mutation_create_person, \
    mutation_person_add_exact_match_person

import muziekweb_api
from importers.audio_object import get_person_information


def import_artist(artist_id: str):
    """Import an artist from Muziekweb and import it to the CE. If the com
    Returns a dictionary:
        {"musiccomposition_id": musiccomp_ceid,
         "person_ids": composer_ids}
    TODO: This code is duplicated in audio_object.import_tracks, and should be abstracted out
    """
    persons = get_artist(artist_id)

    list_person_ids = []
    for person in persons:
        print("Inserting new person {} in Trompa CE\n".format(person.name))

        response = trompace.connection.submit_query(mutation_create_person(**person.as_dict()), auth_required=True)

        person.identifier = response["data"]["CreatePerson"]["identifier"]
        list_person_ids.append(person.identifier)

    for from_id, to_id in itertools.permutations(list_person_ids, 2):
        query = mutation_person_add_exact_match_person(from_id, to_id)
        response = trompace.connection.submit_query(query, auth_required=True)
        print(f"   - Linking Person {from_id} to Person {to_id} done.")

    # Return CE ID of the muziekweb Person
    mw_person = [p for p in persons if p.contributor == "https://www.muziekweb.nl"]
    if mw_person:
        return mw_person[0]
    else:
        return None


def get_artist(artist_id: str):
    """Query muziekweb api and parse result
    TODO: This code currently skips the check for the artist being a group
    """
    artist = muziekweb_api.get_artist_information(artist_id)
    perf_name = artist.getElementsByTagName('PresentationName')[0].firstChild.data
    perf_text = perf_name.replace(' ', '-')
    unif_style = artist.getElementsByTagName('Catalogue')[0].firstChild.data.split(' ')[0]
    persons = get_person_information(artist, perf_name, artist_id, perf_text, unif_style)
    return persons


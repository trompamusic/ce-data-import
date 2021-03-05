"""
Muziekweb artist importer
"""
from typing import Optional

import trompace as ce
from SPARQLWrapper import SPARQLWrapper, JSON
from trompace.connection import submit_query
from trompace.mutations.person import mutation_update_person, mutation_create_person

from models import CE_Person
from trompace_local import GLOBAL_CONTRIBUTOR, GLOBAL_IMPORTER_REPO, GLOBAL_PUBLISHER, lookupIdentifier


async def import_artist(keys: list):
    """
    Imports artists from Muziekweb for all given keys into the Trompa CE.
    """
    for key in keys:
        print(f"Retrieving artist with key {key} from Muziekweb")
        # Get data from Muziekweb
        artist = await get_mw_artist(key)

        if artist is None:
            print(f"No data received for {key}")
            continue

        artist.identifier = await lookupIdentifier("Person", artist.source)

        if artist.identifier is not None:
            print(f"Updating record {artist.identifier} in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_update_person(**artist.as_dict()))
            artist.identifier = response["data"]["UpdatePerson"]["identifier"]
        else:
            print("Inserting new record in Trompa CE", end="")
            response = await ce.connection.submit_query(mutation_create_person(**artist.as_dict()))
            artist.identifier = response["data"]["CreatePerson"]["identifier"]

        if artist.identifier is None:
            print(" - failed.")
        else:
            print(" - success.")

    print("Importing artists done.")


async def get_mw_artist(key: str) -> Optional[CE_Person]:
    sparql = SPARQLWrapper(
        "https://api.data.muziekweb.nl/datasets/muziekweborganization/Muziekweb/services/Muziekweb/sparql")
    sparql.setReturnFormat(JSON)
    qry = f"""PREFIX schema: <http://schema.org/>
    PREFIX vocab: <https://data.muziekweb.nl/vocab/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?url ?name ?birthYear ?deathYear where {{
        BIND(<https://data.muziekweb.nl/Link/{key}> as ?url)
        ?url vocab:beginYear ?birthYear;
            vocab:endYear ?deathYear;
            rdfs:label ?name.
    }}"""
    sparql.setQuery(qry)

    result = sparql.query().convert()["results"]["bindings"]

    if len(result) > 0:
        # Now get Muziekweb data
        person = CE_Person(
            identifier=None,
            name=result[0]["name"]["value"],
            url=result[0]["url"]["value"],
            contributor=GLOBAL_CONTRIBUTOR,
            creator=GLOBAL_IMPORTER_REPO,
        )

        person.publisher = GLOBAL_PUBLISHER
        person.description = None
        person.birthDate = result[0]["birthYear"]["value"]
        person.deathDate = result[0]["deathYear"]["value"]

        return person

    return None

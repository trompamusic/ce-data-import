# Transform items to GraphQL queries
# Python GQL libraries (quiz, gql) don't appear to support
# mutations with their DSLs yet, so we just do it manually
import json

from trompamb import wikidata

MUTATION = '''
mutation {{
  {mutation}
}}
'''

CREATE_PERSON = '''
CreatePerson(
{parameters}
) {{
  identifier
}}
'''


class StringConstant:
    """Some values in GraphQL are constants, not strings, and so they shouldn't
    be encoded or have quotes put around them. Use this to represent a constant
    and it won't be quoted in the query"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


def get_wikidata_url(mb_artist):
    # The relation type for artist-url relation type
    wikidata_mb_rel_type = "689870a4-a1e4-4912-b17f-7b2664215698"
    for l in mb_artist.get("url-relation-list", []):
        if l["type-id"] == wikidata_mb_rel_type:
            return l["target"]
    return None


def transform_artist(mb_artist):
    """Transform a musicbrainz artist to a CreatePerson mutation for the CE"""

    # possible languages: en,es,ca,nl,de,fr

    wikidata_url = get_wikidata_url(mb_artist)
    description = ""
    if wikidata_url:
        description = wikidata.get_description_for_wikidata(wikidata_url)

    artist_name = mb_artist["name"]
    args = {
        "title": artist_name,
        "name": artist_name,
        "publisher": "https://musicbrainz.org",
        "contributor": "https://musicbrainz.org",
        "creator": "https://musicbrainz.org",
        "source": "https://musicbrainz.org/artist/{}".format(mb_artist["id"]),
        "subject": "artist",
        "description": description,
        "format": "text/html",  # an artist doesn't have a mimetype, use the mimetype of the source (musicbrainz page)
        "language": StringConstant("en"),
            }
    return mutation_artist(**args)


def make_parameters(**kwargs):
    encoder = json.JSONEncoder()
    parts = []
    for k, v in kwargs.items():
        if isinstance(v, StringConstant):
            value = v.value
        else:
            value = encoder.encode(v)
        parts.append("{}: {}".format(k, value))
    return "\n".join(parts)


def mutation_artist(**kwargs):
    create_person = CREATE_PERSON.format(parameters=make_parameters(**kwargs))
    return MUTATION.format(mutation=create_person)

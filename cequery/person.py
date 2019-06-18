# Transform items to GraphQL queries
# Python GQL libraries (quiz, gql) don't appear to support
# mutations with their DSLs yet, so we just do it manually


from cequery import StringConstant, make_parameters

from cequery import wikipedia

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
  name
}}
'''


def get_wikidata_url(mb_artist):
    # The relation type for artist-url relation type
    wikidata_mb_rel_type = "689870a4-a1e4-4912-b17f-7b2664215698"
    for l in mb_artist.get("url-relation-list", []):
        if l["type-id"] == wikidata_mb_rel_type:
            return l["target"]
    return None


def transform_data_artist(composer_args):
    """Transform data from scraped composers data file"""

    return mutation_artist(**composer_args)


def transform_musicbrainz_artist(mb_artist):
    """Transform a musicbrainz artist to a CreatePerson mutation for the CE"""

    # possible languages: en,es,ca,nl,de,fr

    wikidata_url = get_wikidata_url(mb_artist)
    description = ""
    if wikidata_url:
        description = wikipedia.get_description_for_wikidata(wikidata_url)

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


def mutation_artist(**kwargs):
    create_person = CREATE_PERSON.format(parameters=make_parameters(**kwargs))
    return MUTATION.format(mutation=create_person)

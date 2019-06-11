import json

from cequery import wikidata
from cequery.transform_musicbrainz import get_wikidata_url, StringConstant

MUTATION = '''mutation {{
  {mutation}
}}
'''

CREATE_MUSIC_COMPOSITION = '''
CreateMusicComposition(
  {parameters}
) {{
  relation
}}
'''

ADD_MUSIC_COMPOSITION_COMPOSER = '''
AddMusicCompositionComposer(
  from: {identifier: {{work_id}}}
  to: {identifier: {{person_id}}}
)
'''


def get_composer_rel(mb_work):
    # The relation type for artist-url relation type
    composer_rel_type = "d59d99ea-23d4-4a80-b066-edca32ee158f"
    for l in mb_artist.get("artist-relation-list", []):
        if l["type-id"] == composer_rel_type:
            return l["artist"]
    return None


def link_composition_composer(composition_identifier, composer_identifier):
    add_music_composition_composer = ADD_MUSIC_COMPOSITION_COMPOSER.format(work_id=composition_identifier,
                                                                           person_id=composer_identifier)
    return MUTATION.format(mutation=add_music_composition_composer)


def transform_musicbrainz_work(mb_work):
    """Transform a musicbrainz artist to a CreatePerson mutation for the CE"""

    # possible languages: en,es,ca,nl,de,fr

    wikidata_url = get_wikidata_url(mb_artist)
    description = ""
    if wikidata_url:
        description = wikidata.get_description_for_wikidata(wikidata_url)

    artist = get_composer_rel(mb_work)
    if not artist:
        print("unknown artist")
        artist = {"name": "Unknown"}

    work_name = mb_work["name"]
    args = {
        "title": work_name,
        "name": work_name,
        "publisher": "https://musicbrainz.org",
        "contributor": "https://musicbrainz.org",
        "creator": artist,
        "source": "https://musicbrainz.org/work/{}".format(mb_work["id"]),
        "subject": "artist",
        "description": description,
        "format": "text/html",  # a work doesn't have a mimetype, use the mimetype of the source (musicbrainz page)
        # TODO: do works have a languange?
        "language": StringConstant("en"),
            }
    return mutation_composition(**args)


def transform_data_composition(composition):
    """Transform a work from a data file to a CreateMusicComposition mutation for the CE"""

    args = {
        "title": composition["Title"],
        "name": composition["Title"],
        "relation": composition["Relation"],
        "contributor": composition["Contributor"],
        "creator": composition["Creator"],
        "description": composition["Description"],
        "source": composition["Source"],
        "publisher": composition["Publisher"],
        "subject": composition["Subject"],
        "format": composition["Format"],
        "language": StringConstant(composition["Language"]),
            }
    return mutation_composition(**args)


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


def mutation_composition(**kwargs):
    create_music_composition = CREATE_MUSIC_COMPOSITION.format(parameters=make_parameters(**kwargs))
    return MUTATION.format(mutation=create_music_composition)

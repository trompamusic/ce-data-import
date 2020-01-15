from cequery import StringConstant, make_parameters
from cequery import wikipedia
from cequery.person import get_wikidata_url

MUTATION = '''mutation {{
  {mutation}
}}
'''

CREATE_MUSIC_COMPOSITION = '''
CreateMusicComposition(
  {parameters}
) {{
  identifier
  name
  relation
}}
'''

UPDATE_MUSIC_COMPOSITION = '''
UpdateMusicComposition(
  {parameters}
) {{
  identifier
  name
  relation
}}
'''

MERGE_COMPOSITION_AUTHOR = '''
MergeCreativeWorkInterfaceAuthor(
  from: {{identifier: "{composition_id}"}}
  to: {{identifier: "{composer_id}"}}
)
{{
    from {{
        identifier
    }}
  to {{
        identifier
    }}
}}
'''

ADD_COMPOSITION_AUTHOR = '''
AddCreativeWorkInterfaceAuthor(
  from: {{identifier: "{composition_id}"}}
  to: {{identifier: "{composer_id}"}}
)
{{
  from {{
        identifier
  }}
  to {{
        identifier
  }}
}}
'''

REMOVE_COMPOSITION_AUTHOR = '''
RemoveCreativeWorkInterfaceAuthor(
  from: {{identifier: "{composition_id}"}}
  to: {{identifier: "{composer_id}"}}
)
{{
  from {{
        identifier
  }}
  to {{
        identifier
  }}
}}
'''


def get_mutation_merge_composition_author(composition_id, composer_id):
    query = MERGE_COMPOSITION_AUTHOR.format(composition_id=composition_id, composer_id=composer_id)
    return MUTATION.format(mutation=query)


def get_query_add_composition_author(composition_id, composer_id):
    query = ADD_COMPOSITION_AUTHOR.format(composition_id=composition_id, composer_id=composer_id)
    return MUTATION.format(mutation=query)


def get_query_remove_composition_author(composition_id, composer_id):
    query = REMOVE_COMPOSITION_AUTHOR.format(composition_id=composition_id, composer_id=composer_id)
    return MUTATION.format(mutation=query)


def get_composer_rel(mb_work):
    # The relation type for artist-url relation type
    composer_rel_type = "d59d99ea-23d4-4a80-b066-edca32ee158f"
    for l in mb_artist.get("artist-relation-list", []):
        if l["type-id"] == composer_rel_type:
            return l["artist"]
    return None


def transform_musicbrainz_work(mb_work):
    """Transform a musicbrainz artist to a CreatePerson mutation for the CE"""

    # possible languages: en,es,ca,nl,de,fr

    wikidata_url = get_wikidata_url(mb_artist)
    description = ""
    if wikidata_url:
        description = wikipedia.get_description_for_wikidata(wikidata_url)

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
    create_music_composition = CREATE_MUSIC_COMPOSITION.format(parameters=make_parameters(**args))
    return MUTATION.format(mutation=create_music_composition)


def transform_data_update_composition(identifier, composition):
    """Transform a work from a data file to a UpdateMusicComposition mutation for the CE"""

    # required params: contributor, creator, description, format, language, source,
    # subject, title, name, identifer

    args = _transform_data_create_composition(composition)
    args["identifier"] = identifier
    update_music_composition = UPDATE_MUSIC_COMPOSITION.format(parameters=make_parameters(**args))
    return MUTATION.format(mutation=update_music_composition)


def _transform_data_create_composition(composition):
    """Transform a work from a data file to a CreateMusicComposition mutation for the CE"""

    # required params: contributor, creator, description, format, language, source,
    # subject, title, name

    desc = composition.get("Description",
                           "Composition {} by {}".format(composition["Title"], composition["Creator"]["Name"]))

    args = {
        "title": composition["Title"],
        "name": composition["Title"],
        "contributor": composition["Contributor"],
        "creator": composition["Creator"]["Name"],
        "description": desc,
        "source": composition["Source"],
        # "publisher": composition["Publisher"],
        "subject": composition["Subject"],
        # The format of the source page
        "format": "text/html",
        # The language of the source page
        "language": StringConstant(composition["Language"]),
            }
    return args


def transform_data_create_composition(composition):
    """Transform a work from a data file to a CreateMusicComposition mutation for the CE"""

    args = _transform_data_create_composition(composition)
    create_music_composition = CREATE_MUSIC_COMPOSITION.format(parameters=make_parameters(**args))
    return MUTATION.format(mutation=create_music_composition)


QUERY = '''
query {{
  {query}
}}'''

QUERY_PERSON = '''
  Person(source: "{source}") {{
    identifier
    name
  }}
'''


QUERY_MUSIC_COMPOSITION = '''
  MusicComposition(source: "{source}") {{
    identifier
    name
  }}
'''


def query_person_by_source(source_url):
    """Get a Person from the database that has a given source URL"""
    query_person = QUERY_PERSON.format(source=source_url)
    return QUERY.format(query=query_person)


def query_music_composition_by_source(source_url):
    query_music_composition = QUERY_MUSIC_COMPOSITION.format(source=source_url)
    return QUERY.format(query=query_music_composition)

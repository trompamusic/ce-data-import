
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

QUERY_DIGITAL_DOCUMENT = '''
DigitalDocument(source: "{source}") {{
  identifier
  name
  source
  relation
}}'''


def query_document_by_source(source_url):
    """Get a DigitalDocument that has a given relation/location"""
    query_document = QUERY_DIGITAL_DOCUMENT.format(source=source_url)
    return QUERY.format(query=query_document)


def query_person_by_source(source_url):
    """Get a Person from the database that has a given source URL"""
    query_person = QUERY_PERSON.format(source=source_url)
    return QUERY.format(query=query_person)


def query_music_composition_by_source(source_url):
    query_music_composition = QUERY_MUSIC_COMPOSITION.format(source=source_url)
    return QUERY.format(query=query_music_composition)

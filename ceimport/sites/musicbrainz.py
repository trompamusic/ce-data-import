import requests_cache
from musicbrainzngs import musicbrainz as mb
from requests.adapters import HTTPAdapter

mb.set_useragent('trompa', '0.1')


session = requests_cache.CachedSession()
adapter = HTTPAdapter(max_retries=5)
session.mount("https://", adapter)
session.mount("http://", adapter)


VIAF_REL = 'e8571dcc-35d4-4e91-a577-a3382fd84460'
WIKIDATA_REL = '689870a4-a1e4-4912-b17f-7b2664215698'
IMSLP_REL = '8147b6a2-ad14-4ce7-8f0a-697f9a31f68f'

# Indicates that an artist gwas the composer of a work
COMPOSER_REL = 'd59d99ea-23d4-4a80-b066-edca32ee158f'
# Indicates that a work is a subpart of another work
PARTS_REL = 'ca8d3642-ce5f-49f8-91f2-125d72524e6a'


def get_artist_from_musicbrainz(artist_mbid):
    """
    """
    artist = mb.get_artist_by_id(artist_mbid, includes=['artist-rels'])['artist']

    return artist


def load_artist_from_musicbrainz(artist_mbid):
    """
    """
    artist = get_artist_from_musicbrainz(artist_mbid)
    artist_type = artist.get('type', None)
    if artist_type == 'Group':
        artists = load_group_from_musicbrainz(artist)
    else:
        artists = [load_person_from_musicbrainz(artist)]

    return artists


def load_group_from_musicbrainz(artist):
    """
    """
    artist_relations = artist.get('artist-relation-list', [])
    # Add as first element the group entity itself
    members = [load_person_from_musicbrainz(artist)]
    for relation in artist_relations:
        if relation['type-id'] == '5be4c609-9afa-4ea0-910b-12ffb71e3821':
            member = relation.get('artist', {})
            member = mb.get_artist_by_id(member['id'])['artist']
            mb_person = load_person_from_musicbrainz(member)
            members.append(mb_person)

    return members


def load_person_from_musicbrainz(artist):
    """
    """
    name = artist['name']

    '''TODO: add these items?
        'familyName': family_name,
        'givenName': given_name,
        'publisher': publisher,
        'honorificPrefix': honorific_prefix,
        'honorificSuffix': honorific_suffix,
        'jobTitle': job_title

    Other biblio info? Places, birth date, death date, gender
    language
    If there are aliases in our languages, import them with those languages
    '''

    begin_area = artist.get('begin-area', {}).get('id')
    end_area = artist.get('end-area', {}).get('id')
    birthplace = deathplace = None
    if begin_area:
        birthplace = load_area_from_musicbrainz(begin_area)
    if end_area:
        deathplace = load_area_from_musicbrainz(end_area)
    lifespan = artist.get('life-span')
    born = died = None
    if lifespan:
        born = lifespan.get('begin')
        # This check is for cases where date format from MusiBrainz
        # is not correct
        if born:
            if not all([False for x in born.split("-") if not x.isdigit()]):
                born = None
        died = lifespan.get('end')
        if died:
            if not all([False for x in died.split("-") if not x.isdigit()]):
                died = None

    return {
        # This is the title of the page, so it includes the header
        'title': f'{name} - MusicBrainz',
        'name': name,
        'contributor': 'https://musicbrainz.org',
        'source': f'https://musicbrainz.org/artist/{artist["id"]}',
        'format_': 'text/html',
        'language': 'en',
        'birth_date': born,
        'death_date': died,
        'birthplace': birthplace,
        'deathplace': deathplace
    }


def load_person_relations_from_musicbrainz(artist_mbid):
    # TODO: Don't do this request twice

    artist = mb.get_artist_by_id(artist_mbid, includes=['url-rels'])['artist']
    isnis = artist.get('isni-list', [])

    external_relations = {}

    if isnis:
        # TODO: Could be more than 1
        isni = isnis[0]
        external_relations['isni'] = isni

    rels = artist.get('url-relation-list', [])
    for rel in rels:
        if rel['type-id'] == VIAF_REL:
            external_relations['viaf'] = rel['target']
        elif "worldcat.org" in rel['target']:
            external_relations['worldcat'] = rel['target']
        elif "id.loc.gov" in rel['target']:
            external_relations['loc'] = rel['target']
        elif rel['type-id'] == WIKIDATA_REL:
            external_relations['wikidata'] = rel['target']
        elif rel['type-id'] == IMSLP_REL:
            external_relations['imslp'] = rel['target']

    return external_relations


def load_work_from_musicbrainz(work_mbid):
    work = mb.get_work_by_id(work_mbid, includes=["artist-rels", "work-rels"])['work']

    title = work['title']
    work_dict = {
        # This is the title of the page, so it includes the header
        'title': f'{title} - MusicBrainz',
        'name': title,
        'contributor': 'https://musicbrainz.org',
        'source': f'https://musicbrainz.org/work/{work_mbid}',
        'format_': 'text/html',
        'language': 'en'
    }

    composer_mb_source = None
    composer_mb_id = None
    for artist_rel in work.get('artist-relation-list', []):
        if artist_rel['type-id'] == COMPOSER_REL:
            composer_mb_id = artist_rel['artist']['id']
            composer_mb_source = f"https://musicbrainz.org/artist/{composer_mb_id}"
            # TODO: There might be more than 1 composer?
            break

    # Related works
    parts = []
    for work_rel in work.get('work-relation-list', []):
        if work_rel['type-id'] == PARTS_REL and work_rel['direction'] == 'forward':
            part_work = work_rel['work']
            part_title = part_work['title']
            part_mbid = part_work['id']
            try:
                position = int(work_rel.get('ordering-key'))
            except ValueError:
                print(f"Unknown subpart ordering key: {work_rel.get('ordering-key')}, should be an int")
                position = None
            part = {
                # This is the title of the page, so it includes the header
                'title': f'{part_title} - MusicBrainz',
                'name': part_title,
                'contributor': 'https://musicbrainz.org',
                'source': f'https://musicbrainz.org/work/{part_mbid}',
                'format_': 'text/html',
                'language': 'en',
                'position': position
            }
            parts.append(part)

    return {"work": work_dict,
            "composer_source": composer_mb_source,
            "composer_mbid": composer_mb_id,
            "parts": parts}


def load_area_from_musicbrainz(area_id):
    area = mb.get_area_by_id(area_id)['area']
    name = area['name']
    return {
        # This is the title of the page, so it includes the header
        'title': f'{name} - MusicBrainz',
        'name': name,
        'contributor': 'https://musicbrainz.org',
        'source': f'https://musicbrainz.org/area/{area_id}',
        'format_': 'text/html',
        'language': 'en'
    }


def get_work_mbid_by_imslp_url(imslp_url):
    return _lookup_imslp_url(imslp_url, 'work-rels', _parse_url_work_relation)


def get_artist_mbid_by_imslp_url(imslp_url):
    return _lookup_imslp_url(imslp_url, 'artist-rels', _parse_url_artist_relation)


def _lookup_imslp_url(url, includes, parse_callback):
    # In Musicbrainz, imslp urls are all https:
    if url.startswith("http://"):
        url = url.replace("http:", "https:")

    params = {"fmt": "json", "resource": url,
              "inc": includes}
    headers = {"User-Agent": "trompa importer"}
    r = session.get("https://musicbrainz.org/ws/2/url", params=params, headers=headers)
    if r.status_code == 200:
        return parse_callback(r.json())
    else:
        return None


def _parse_url_artist_relation(response):
    relations = response.get('relations', [])
    if relations:
        return relations[0]['artist']['id']


def _parse_url_work_relation(response):
    """ response is
    {'resource': 'https://imslp.org/wiki/7_Bagatelles,_Op.33_(Beethoven,_Ludwig_van)',
 'relations': [{'source-credit': '',
   'target-credit': '',
   'type-id': '0cc8527e-ea40-40dd-b144-3b7588e759bf',
   'type': 'download for free',
   'end': None,
   'direction': 'forward',
   'ended': False,
   'begin': None,
   'target-type': 'work',
   'work': {'title': '7 Bagatelles, op. 33',
    'attributes': [],
    'languages': [],
    'disambiguation': '',
    'type': None,
    'iswcs': [],
    'type-id': None,
    'id': '94a19e47-2c1d-425b-b4f0-63d62d5bf788',
    'language': None},
   'attribute-values': {},
   'attribute-ids': {},
   'attributes': []}],
 'id': '2d264d6e-5082-46a7-a60a-e2d02ab103e1'}
    """
    relations = response.get('relations', [])
    if relations:
        return relations[0]['work']['id']

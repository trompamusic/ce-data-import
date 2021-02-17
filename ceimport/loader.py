import itertools

from trompace.mutations import person as mutation_person
from trompace.mutations import place as mutation_place
from trompace.mutations import musiccomposition as mutation_musiccomposition
from trompace.mutations import mediaobject as mutation_mediaobject
from trompace.queries import person as query_person
from trompace.queries import musiccomposition as query_musiccomposition
from trompace.queries import mediaobject as query_mediaobject

from ceimport import connection, logger
from ceimport.sites import musicbrainz, cpdl
from ceimport.sites import viaf
from ceimport.sites import imslp
from ceimport.sites import wikidata
from ceimport.sites import loc
from ceimport.sites import worldcat
from ceimport.sites import isni


CREATOR_URL = "https://github.com/trompamusic/ce-data-import/tree/master"


def load_artist_from_musicbrainz(artist_mbid):
    logger.info("Importing musicbrainz artist %s", artist_mbid)
    persons = []
    mb_person = musicbrainz.load_person_from_musicbrainz(artist_mbid)
    persons.append(mb_person)

    rels = musicbrainz.load_person_relations_from_musicbrainz(artist_mbid)
    if 'viaf' in rels:
        viaf_person = viaf.load_person_from_viaf(rels['viaf'])
        persons.append(viaf_person)
    if 'imslp' in rels:
        # TODO: If there are more rels in imslp that aren't in MB we could use them here
        imslp_person = imslp.api_composer(rels['imslp'])
        persons.append(imslp_person)
    if 'worldcat' in rels:
        worldcat_person = worldcat.load_person_from_worldcat(rels['worldcat'])
        persons.append(worldcat_person)
    if 'loc' in rels:
        loc_person = loc.load_person_from_loc(rels['loc'])
        persons.append(loc_person)
    if 'isni' in rels:
        isni_url = f"https://isni.org/isni/{rels['isni']}"
        isni_person = isni.load_person_from_isni(isni_url)
        persons.append(isni_person)
    if 'wikidata' in rels:
        wd_person = wikidata.load_person_from_wikidata(rels['wikidata'])
        if wd_person:
            persons.append(wd_person)
        wp_person = wikidata.load_person_from_wikipedia(rels['wikidata'], 'en')
        if wp_person:
            persons.append(wp_person)

    # dedup by source
    ret = []
    seen = set()
    for p in persons:
        if 'source' in p:
            if p['source'] not in seen:
                ret.append(p)
                seen.add(p['source'])
    return ret


def load_artist_from_imslp(url):
    logger.info("Importing imslp artist %s", url)
    if "Category:" not in url:
        raise Exception("Url should be an imslp Category: url")

    if url.startswith("https://imslp.org"):
        url = "/".join(url.split("/")[4:])

    people = []

    imslp_person = imslp.api_composer(url)
    if imslp_person:
        people.append(imslp_person)

    rels = imslp.api_composer_get_relations(url)
    if 'worldcat' in rels:
        worldcat_person = worldcat.load_person_from_worldcat(rels['worldcat'])
        people.append(worldcat_person)
    if 'viaf' in rels:
        viaf_person = viaf.load_person_from_viaf(rels['viaf'])
        people.append(viaf_person)
    if 'wikipedia' in rels:
        wikidata_id = wikidata.get_wikidata_id_from_wikipedia_url(rels['wikipedia'])
        if wikidata_id:
            wd_person = wikidata.load_person_from_wikidata(rels['wikidata'])
            if wd_person:
                people.append(wd_person)
            wp_person = wikidata.load_person_from_wikipedia(rels['wikidata'], 'en')
            if wp_person:
                people.append(wp_person)
    if 'musicbrainz' in rels:
        mb_person = musicbrainz.load_person_from_musicbrainz(rels['musicbrainz'])
        people.append(mb_person)
    if 'isni' in rels:
        isni_person = isni.load_person_from_isni(rels['isni'])
        people.append(isni_person)
    if 'loc' in rels:
        loc_person = loc.load_person_from_loc(rels['loc'])
        people.append(loc_person)

    # If no link to musicbrainz from imslp, do a reverse lookup in musicbrainz to see if it's there
    if 'musicbrainz' not in rels:
        artist_mbid = musicbrainz.get_artist_mbid_by_imslp_url(url)
        # TODO: If the artist exists in MB, then we should also import all of the other
        #  relationships that exist, by using `load_artist_from_musicbrainz`
        if artist_mbid:
            mb_person = musicbrainz.load_person_from_musicbrainz(artist_mbid)
            people.append(mb_person)

    # dedup by source
    ret = []
    seen = set()
    for p in people:
        if 'source' in p:
            if p['source'] not in seen:
                ret.append(p)
                seen.add(p['source'])
    return ret


def get_existing_person_by_source(source) -> str:
    """Returns an identifier of the thing with the given source, else None"""
    query_by_source = query_person.query_person(source=source)
    resp = connection.submit_request(query_by_source)
    person = resp.get('data', {}).get('Person', [])
    if not person:
        return None
    else:
        return person[0]['identifier']


def get_existing_mediaobject_by_source(source) -> str:
    """Returns an identifier of the thing with the given source, else None"""
    query_by_source = query_mediaobject.query_mediaobject(source=source)
    resp = connection.submit_request(query_by_source)
    mediaobject = resp.get('data', {}).get('MediaObject', [])
    if not mediaobject:
        return None
    else:
        return mediaobject[0]['identifier']


def create_mediaobject(mediaobject):
    mediaobject["creator"] = CREATOR_URL
    mutation_create = mutation_mediaobject.mutation_create_media_object(**mediaobject)
    resp = connection.submit_request(mutation_create)
    # TODO: If this query fails?
    return resp['data']['CreateMediaObject']['identifier']


def create_person(person):
    """Create a person object
    Arguments:
        person: a dictionary where keys are the parameters to the `mutation_create_person` function

    If `person` includes the keys 'birthplace' or 'deathplace', these items are extracted out,
    used to create a Place object, and then linked to the person
    """
    person["creator"] = CREATOR_URL

    birthplace = None
    if 'birthplace' in person:
        birthplace = person['birthplace']
        del person['birthplace']
    deathplace = None
    if 'deathplace' in person:
        deathplace = person['deathplace']
        del person['deathplace']

    mutation_create = mutation_person.mutation_create_person(**person)
    resp = connection.submit_request(mutation_create)
    # TODO: If this query fails?
    person_id = resp['data']['CreatePerson']['identifier']

    if birthplace:
        birthplace["creator"] = CREATOR_URL
        mutation_create = mutation_place.mutation_create_place(**birthplace)
        resp = connection.submit_request(mutation_create)
        birthplace_id = resp['data']['CreatePlace']['identifier']
        mutation_merge = mutation_place.mutation_merge_person_birthplace(person_id, birthplace_id)
        connection.submit_request(mutation_merge)

    if deathplace:
        deathplace["creator"] = CREATOR_URL
        mutation_create = mutation_place.mutation_create_place(**deathplace)
        resp = connection.submit_request(mutation_create)
        deathplace_id = resp['data']['CreatePlace']['identifier']
        mutation_merge = mutation_place.mutation_merge_person_deathplace(person_id, deathplace_id)
        connection.submit_request(mutation_merge)

    return person_id


def create_place(place):
    place["creator"] = CREATOR_URL
    mutation_create = mutation_place.mutation_create_place(**place)
    resp = connection.submit_request(mutation_create)
    # TODO: If this query fails?
    return resp['data']['CreatePlace']['identifier']


def create_musiccomposition(musiccomposition):
    musiccomposition["creator"] = CREATOR_URL
    mutation_create = mutation_musiccomposition.mutation_create_music_composition(**musiccomposition)
    resp = connection.submit_request(mutation_create)
    # TODO: If this query fails?
    return resp['data']['CreateMusicComposition']['identifier']


def link_musiccomposition_and_parts(musiccomposition_id, part_ids):
    for part_id in part_ids:
        query = mutation_musiccomposition.mutation_merge_music_composition_included_composition(musiccomposition_id, part_id)
        connection.submit_request(query)
        query = mutation_musiccomposition.mutation_merge_music_composition_has_part(musiccomposition_id, part_id)
        connection.submit_request(query)


def link_musiccomposition_and_composers(musiccomposition_id, composer_ids):
    for composer_id in composer_ids:
        query = mutation_musiccomposition.mutation_merge_music_composition_composer(musiccomposition_id, composer_id)
        connection.submit_request(query)


def link_person_ids(person_ids):
    for from_id, to_id in itertools.permutations(person_ids, 2):
        query = mutation_person.mutation_person_add_exact_match_person(from_id, to_id)
        connection.submit_request(query)


def link_musiccomposition_and_mediaobject(composition_id, mediaobject_id):
    query = mutation_mediaobject.mutation_merge_mediaobject_example_of_work(mediaobject_id, composition_id)
    connection.submit_request(query)


def create_persons_and_link(persons):
    # TODO: This returns all person ids that we created, but there could be other
    #  ids in the database of this person, we should link those and return them too
    person_ids = []
    for p in persons:
        p_id = get_or_create_person(p)
        person_ids.append(p_id)

    # Join together all persons
    link_person_ids(person_ids)
    return person_ids


def get_existing_musiccomposition_by_source(source) -> str:
    """Returns an identifier of the thing with the given source, else None"""
    query_by_source = query_musiccomposition.query_musiccomposition(source=source)
    resp = connection.submit_request(query_by_source)
    mc = resp.get('data', {}).get('MusicComposition', [])
    if not mc:
        return None
    else:
        return mc[0]['identifier']


def get_or_create_person(person):
    existing = get_existing_person_by_source(person['source'])
    if existing:
        return existing
    return create_person(person)


def get_or_create_musiccomposition(musiccomposition):
    source = musiccomposition['source']
    existing = get_existing_musiccomposition_by_source(source)
    if existing:
        return existing

    return create_musiccomposition(musiccomposition)


def get_or_create_mediaobject(mediaobject):
    source = mediaobject['source']
    existing = get_existing_mediaobject_by_source(source)
    if existing:
        return existing

    return create_mediaobject(mediaobject)


def load_musiccomposition_from_musicbrainz(work_mbid):
    logger.info("Importing musicbrainz work %s", work_mbid)
    meta = musicbrainz.load_work_from_musicbrainz(work_mbid)

    # Create composition, or get its id if it already exists
    musiccomp_ceid = get_or_create_musiccomposition(meta['work'])

    # Import the work's composer if it doesn't exist
    # This will hit MB for the artist lookup, but won't write to the CE if the composer already exists
    composer = meta['composer_mbid']
    # Returns all composer ids of all exactMatches for this composer
    persons = load_artist_from_musicbrainz(composer)
    composer_ids = create_persons_and_link(persons)

    all_part_ids = []
    # For each part, import the part and then link it to the main work
    for part in meta['parts']:
        part_id = get_or_create_musiccomposition(part)
        all_part_ids.append(part_id)

    link_musiccomposition_and_parts(musiccomp_ceid, all_part_ids)
    link_musiccomposition_and_composers(musiccomp_ceid, composer_ids)
    # Link composer to all parts
    for part_id in all_part_ids:
        link_musiccomposition_and_composers(part_id, composer_ids)


def load_musiccomposition_from_imslp_url(imslp_url, need_xml):
    """Load a MusicComposition from a single page on IMSLP,
    and also load any musicxml files as MediaObjects
    TODO: Should be able to specify what to download, e.g. a specific PDF, or all files, or only music xmls
    TODO: Should be able to specify a Special:ReverseLookup url which gives the composition and file
    """

    logger.info("Importing imslp work %s", imslp_url)
    composition, composer_url, xml_objects = imslp.get_composition_page(imslp_url)

    if not need_xml or xml_objects:
        composition_id = get_or_create_musiccomposition(composition)
        composer_ids = load_artist_from_imslp(composer_url)
        link_musiccomposition_and_composers(composition_id, composer_ids)

        for xml in xml_objects:
            mediaobject_id = get_or_create_mediaobject(xml)
            link_musiccomposition_and_mediaobject(composition_id, mediaobject_id)
    else:
        logger.info(" - No xml files, skipping")


def import_cpdl_composers_for_category(cpdl_category):
    """Given a category in CPDL, find all of its works. Then, filter to only include works
    with a musicxml file and get a unique list of composers for these works.
    For each composer, import it along with links to imslp and wikipedia if they exist."""

    titles = cpdl.get_titles_in_category(cpdl_category)
    wikitext = cpdl.get_wikitext_for_titles(titles)
    xmlwikitext = cpdl.get_works_with_xml(wikitext)
    composers = cpdl.get_composers_for_works(xmlwikitext)
    composerwikitext = cpdl.get_wikitext_for_titles(composers)

    total = len(composerwikitext)
    for i, composer in enumerate(composerwikitext, 1):
        logger.info("Importing CPDL composer %s/%s %s", i, total, composer['title'])
        person = cpdl.composer_wikitext_to_person(composer)
        person_cpdl = person['cpdl']
        persons = [person_cpdl]

        if person['imslp']:
            person_imslp = load_artist_from_imslp(person['imslp'])
            persons.extend(person_imslp)
        if person['wikipedia']:
            wikidata_id = wikidata.get_wikidata_id_from_wikipedia_url(person['wikipedia'])
            if wikidata_id:
                wd_person = wikidata.load_person_from_wikidata(wikidata_id)
                if wd_person:
                    persons.append(wd_person)
                wp_person = wikidata.load_person_from_wikipedia(wikidata_id, 'en')
                if wp_person:
                    persons.append(wp_person)
        create_persons_and_link(persons)


def import_cpdl_works_for_category(cpdl_category):
    """Given a category in CPDL, find all of its works. Then, filter to only include works
    with a musicxml file. Import each of these works and the xml files.
    This assumes that import_cpdl_composers_for_category has been run first and that Person
    objects exist in the CE for each Composer"""

    titles = cpdl.get_titles_in_category(cpdl_category)
    wikitext = cpdl.get_wikitext_for_titles(titles)
    xmlwikitext = cpdl.get_works_with_xml(wikitext)

    xmlwikitext = xmlwikitext[-4000:]
    total = len(xmlwikitext)
    for i, work in enumerate(xmlwikitext, 1):
        logger.info("Importing CPDL work %s/%s %s", i, total, work['title'])
        composition = cpdl.composition_wikitext_to_music_composition(work)
        composer = composition['composer']
        if composer is not None:
            source = f'https://cpdl.org/wiki/index.php/{composer.replace(" ", "_")}'
            existing_composer_ceid = get_existing_person_by_source(source)
            if existing_composer_ceid:
                musiccomp_ceid = get_or_create_musiccomposition(composition['work'])
                link_musiccomposition_and_composers(musiccomp_ceid, [existing_composer_ceid])
                mediaobjects = cpdl.composition_wikitext_to_mediaobjects(work)
                for mo in mediaobjects:
                    mediaobject_ceid = get_or_create_mediaobject(mo)
                    link_musiccomposition_and_mediaobject(composition_id=musiccomp_ceid,
                                                          mediaobject_id=mediaobject_ceid)
            else:
                logger.info(" - missing composer?")

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
        imslp_url = rels['imslp']
        imslp_person = imslp.api_composer(imslp_url.replace("https://imslp.org/wiki/", "").replace("_", " "))
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
        wd_person = wikidata.load_person_from_wikidata_url(rels['wikidata'])
        if wd_person:
            persons.append(wd_person)
        wp_person = wikidata.load_person_from_wikipedia_wikidata_url(rels['wikidata'], 'en')
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


def link_musiccomposition_exactmatch(musiccomposition_ids):
    for from_id, to_id in itertools.permutations(musiccomposition_ids, 2):
        query = mutation_musiccomposition.mutation_merge_music_composition_exact_match(from_id, to_id)
        connection.submit_request(query)


def link_person_ids(person_ids):
    for from_id, to_id in itertools.permutations(person_ids, 2):
        query = mutation_person.mutation_person_add_exact_match_person(from_id, to_id)
        connection.submit_request(query)


def link_musiccomposition_and_mediaobject(composition_id, mediaobject_id):
    query = mutation_mediaobject.mutation_merge_mediaobject_example_of_work(mediaobject_id, composition_id)
    connection.submit_request(query)


def link_mediaobject_was_derived_from(source_id, derived_id):
    query = mutation_mediaobject.mutation_merge_media_object_wasderivedfrom(derived_id, source_id)
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

    return {"musiccomposition_id": musiccomp_ceid,
            "part_ids": all_part_ids,
            "person_ids": composer_ids}


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
            wd_person = wikidata.load_person_from_wikidata_url(rels['wikidata'])
            if wd_person:
                people.append(wd_person)
            wp_person = wikidata.load_person_from_wikipedia_wikidata_url(rels['wikidata'], 'en')
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


def load_musiccomposition_from_imslp_by_file(reverselookup):
    """Using an IMSLP Special:ReverseLookup url, find the composition and import
       - composer
       - work
       - file
    """
    if not reverselookup.startswith("https://imslp.org/wiki/Special:ReverseLookup/"):
        raise ValueError("Should be a Special:ReverseLookup url")

    composition, filename = imslp.get_composition_and_filename_from_permalink(reverselookup)
    # The composition url will end with a #anchor, remove it
    if "#" in composition:
        composition = composition[:composition.index("#")]
    load_musiccomposition_from_imslp_name(composition, load_files=False)

    # Once we loaded the composition, we look it up again to get the id
    url = "https://imslp.org/wiki/" + composition.replace(" ", "_")
    composition_id = get_existing_musiccomposition_by_source(url)
    print("got id", composition_id)

    wikitext = imslp.get_wiki_content_for_pages([composition])
    if composition_id:
        if wikitext:
            file = imslp.get_mediaobject_for_filename(wikitext[0], filename.replace(" ", "_"))
            if file:
                mediaobject_ceid = get_or_create_imslp_mediaobject(file)
                link_musiccomposition_and_mediaobject(composition_id=composition_id,
                                                      mediaobject_id=mediaobject_ceid)
    else:
        logger.info(" - cannot find composition after importing it once")


def get_or_create_imslp_mediaobject(mediaobject):
    """Look for an existing mediaobject based on the url field (permalink)
    otherwise create one"""
    source = mediaobject['url']
    existing = get_existing_mediaobject_by_source(source)
    if existing:
        return existing

    return create_mediaobject(mediaobject)


def load_musiccomposition_from_imslp_name(imslp_name, load_files=True):
    """Load a MusicComposition from a single page on IMSLP,
    and also load any musicxml files as MediaObjects and any related PDFs
    """

    logger.info("Importing imslp work %s", imslp_name)
    work = imslp.api_work(imslp_name)
    musiccomposition = work["work"]
    composer = work["composer"]
    musicbrainz_work_id = work["musicbrainz_work_id"]

    if composer:
        composition_id = get_or_create_musiccomposition(musiccomposition)

        composer_source = f'https://imslp.org/wiki/{composer.replace(" ", "_")}'

        existing_composer_ceid = get_existing_person_by_source(composer_source)
        if not existing_composer_ceid:
            persons = load_artist_from_imslp(composer)
            create_persons_and_link(persons)
            existing_composer_ceid = get_existing_person_by_source(composer_source)

        link_musiccomposition_and_composers(composition_id, [existing_composer_ceid])

        if musicbrainz_work_id:
            mb_work = load_musiccomposition_from_musicbrainz(musicbrainz_work_id)
            mb_work_ceid = mb_work["musiccomposition_id"]
            link_musiccomposition_exactmatch([composition_id, mb_work_ceid])

        if not load_files:
            return

        wikitext = imslp.get_wiki_content_for_pages([imslp_name])
        files = imslp.files_for_work(wikitext[0])
        # We expect to see just one xml file, and maybe one pdf
        # TODO, there could be more than one, we need to support this too
        if len(files) == 0:
            logger.info(" - expected at least one file but got none")
        if len(files) == 1:
            file = files[0]
            if "XML" not in file["description"]:
                logger.info(" - Only got one file but it's not an xml, not sure what to do")
            else:
                xmlmediaobject_ceid = get_or_create_imslp_mediaobject(file)
                link_musiccomposition_and_mediaobject(composition_id=composition_id,
                                                      mediaobject_id=xmlmediaobject_ceid)
        else:
            xmlfile = [f for f in files if "XML" in f["description"]]
            pdffiles = [f for f in files if f["name"].endswith("pdf")]
            if not xmlfile or not pdffiles:
                logger.info(" - expected one xml and some pdfs, but this isn't the case")
                print(files)
            else:
                xmlfile = xmlfile[0]
                xmlmediaobject_ceid = get_or_create_imslp_mediaobject(xmlfile)
                link_musiccomposition_and_mediaobject(composition_id=composition_id,
                                                      mediaobject_id=xmlmediaobject_ceid)

                logger.info(" - got %s pdf files, importing each of them", len(pdffiles))
                for pdffile in pdffiles:
                    pdfmediaobject_ceid = get_or_create_imslp_mediaobject(pdffile)
                    link_musiccomposition_and_mediaobject(composition_id=composition_id,
                                                          mediaobject_id=pdfmediaobject_ceid)

                    # In IMSLP, a PDF that comes linked with an XML file is a rendering of that file ,
                    # so the pdf is derived from the score
                    # TODO: We should check if this is the case all the time.
                    link_mediaobject_was_derived_from(source_id=xmlmediaobject_ceid,
                                                      derived_id=pdfmediaobject_ceid)
    else:
        logger.info(" - No composer??, skipping")


def import_cpdl_composer_wikitext(composer_wikitext):
    person = cpdl.composer_wikitext_to_person(composer_wikitext)
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
            wp_person = wikidata.load_person_from_wikdata(wikidata_id, 'en')
            if wp_person:
                persons.append(wp_person)
    create_persons_and_link(persons)


def import_cpdl_composer(composer_name):
    """Import a single composer"""
    composerwikitext = cpdl.get_wikitext_for_titles([composer_name])
    if composerwikitext:
        composer = composerwikitext[0]
        logger.info("Importing CPDL composer %s", composer['title'])
        import_cpdl_composer_wikitext(composer)
        source = f'https://cpdl.org/wiki/index.php/{composer["title"].replace(" ", "_")}'
        existing_composer_ceid = get_existing_person_by_source(source)
        return existing_composer_ceid
    else:
        return None


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
        import_cpdl_composer_wikitext(composer)


def import_cpdl_work_wikitext(work_wikitext):
    composition = cpdl.composition_wikitext_to_music_composition(work_wikitext)
    composer = composition['composer']
    if composer is not None:
        source = f'https://cpdl.org/wiki/index.php/{composer.replace(" ", "_")}'
        existing_composer_ceid = get_existing_person_by_source(source)
        if not existing_composer_ceid:
            existing_composer_ceid = import_cpdl_composer(composer)
        if existing_composer_ceid:
            musiccomp_ceid = get_or_create_musiccomposition(composition['work'])
            link_musiccomposition_and_composers(musiccomp_ceid, [existing_composer_ceid])
            mediaobjects = cpdl.composition_wikitext_to_mediaobjects(work_wikitext)
            for mo in mediaobjects:
                xml = mo["xml"]
                xmlmediaobject_ceid = get_or_create_mediaobject(xml)
                link_musiccomposition_and_mediaobject(composition_id=musiccomp_ceid,
                                                      mediaobject_id=xmlmediaobject_ceid)
                if "pdf" in mo and mo["pdf"] is not None:
                    pdf = mo["pdf"]
                    pdfmediaobject_ceid = get_or_create_mediaobject(pdf)
                    link_musiccomposition_and_mediaobject(composition_id=musiccomp_ceid,
                                                          mediaobject_id=pdfmediaobject_ceid)
                    # In CPDL, we know that PDFs are generated from the source xml file
                    # TODO: Are there any situations where this isn't the case?
                    link_mediaobject_was_derived_from(source_id=xmlmediaobject_ceid, derived_id=pdfmediaobject_ceid)
        else:
            logger.info(" - missing composer?")


def import_cpdl_work(work_name):
    """Import a single work"""
    wikitext = cpdl.get_wikitext_for_titles([work_name])
    for work in wikitext:
        logger.info("Importing CPDL work %s", work['title'])
        import_cpdl_work_wikitext(work)


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
        import_cpdl_work_wikitext(work)

import argparse
import itertools
import json
import logging
from urllib.parse import urlparse

import musicbrainzngs as mb

import cequery
import cequery.work
import cequery.document
import cequery.person
from cequery import connection, StringConstant

mb.set_useragent('TROMPA', '0.1')
logger = logging.getLogger('corpus_import')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


def add_documents(work_identifier, work):
    # contributor, creator, description, format, language, source, subject, title, name, relation, license
    logger.info("Adding documents for work...")
    work_relations = work["Relation"]
    documents = []
    for r in work_relations:
        doc = {"contributor": work["Contributor"],
               "creator": r["Publisher"],
               "description": r.get("Description", "Score for {}".format(work["Title"])),
               "format": r["Format"],
               "language": StringConstant(work["Language"]),
               "source": r["File_url"],
               "subject": work["Subject"],
               "title": work["Title"],
               "name": work["Title"],
               "relation": r["File_url"],
               "license": r["License"]}
        documents.append(doc)

    document_identifiers = []
    for d in documents:
        doc_id = add_or_get_digital_document(d)
        document_identifiers.append(doc_id)

    make_documents_broad_match(document_identifiers)
    join_work_and_documents(work_identifier, document_identifiers)


def add_or_get_digital_document(document):
    logger.info("Adding document")
    query_resp = connection.get_digital_document_by_source(document["source"])
    if len(query_resp) == 0:
        logger.info("  doesn't exist, adding")
        query = cequery.document.transform_data_create_document(document)
        resp = connection.submit_query(query)
        resp_document = resp["data"]["CreateDigitalDocument"]
    elif len(query_resp) == 1:
        logger.info("  exists")
        resp_document = query_resp[0]
    identifier = resp_document["identifier"]
    logger.info("  document id %s", identifier)
    return identifier


def make_documents_broad_match(document_ids):
    """If a work has more than one score, the documents are broadMatches of each other. We should
    create relations between *all permutations* of these documents."""
    for from_id, to_id in itertools.permutations(document_ids, 2):
        query = cequery.document.get_mutation_merge_document_broad_match(from_id, to_id)
        connection.submit_query(query)


def join_work_and_documents(work_identifier, document_identifiers):
    """Mark that a score is a workExample a work"""
    for d_id in document_identifiers:
        query = cequery.document.get_mutation_merge_document_composition(work_identifier, d_id)
        connection.submit_query(query)


def import_or_update_composer(composer):
    """Import metdata for a composer from a datafile"""

    logger.info("Adding composer: %s", composer["name"])
    existing_composer = connection.get_person_by_source(composer["source"])
    if len(existing_composer) == 0:
        logger.info("  doesn't exist, adding")
        query = cequery.person.transform_data_artist(composer)
        resp = connection.submit_query(query)
        person = resp["data"]["CreatePerson"]
    elif len(existing_composer) == 1:
        logger.info("  exists, getting")
        person = existing_composer[0]
    else:
        logger.error("Unexpectedly got more than 1 composer for a given source")

    identifier = person["identifier"]
    logger.info("  composer id: %s", identifier)
    return identifier


def import_or_update_wikipedia_composer(wikipedia_url):
    """Import metadata for a composer from wikipedia"""
    pass


def join_work_composer(work_identifier, composer_identifier):
    """Say that a composer wrote a score"""
    logger.info("joining work %s and composer %s", work_identifier, composer_identifier)

    # Remove any link that is already there (We'd have to do a query anyway to check if it exists,
    # so just do it unconditionally)
    # TODO: Could select this query when getting the work originally to check if we update it
    query = cequery.work.get_mutation_merge_composition_author(work_identifier, composer_identifier)
    connection.submit_query(query)
    logger.info("done")


def _get_composer_data(work, artist_data):
    # required fields: contributor, creator, description, format, language, source, subject, name, title

    author = work["Creator"]["Name"]
    source = work["Creator"]["url"]

    url_parts = urlparse(source)
    creator_url = "{}://{}".format(url_parts.scheme, url_parts.netloc)
    biography = "an Artist"

    data = {"contributor": work["Contributor"],
            "creator": creator_url,
            "description": biography,
            # format of the website
            "format": "text/html",
            # Language of the website
            "language": StringConstant(work["Language"]),
            "publisher": creator_url,
            "source": source,
            "subject": "Composer",
            "name": author,
            "title": author
            }

    return data


def import_or_update_work(work, artist_data):
    source = work["Source"]
    title = work["Title"]
    logger.info("Adding work: %s", title)
    existing_work = connection.get_music_composition_by_source(source)
    if len(existing_work) == 0:
        query = cequery.work.transform_data_create_composition(work)
        resp = connection.submit_query(query)
        music_composition = resp["data"]["CreateMusicComposition"]
        logger.info("  done")
    elif len(existing_work) == 1:
        logger.info("  already exists, updating")
        existing_work = existing_work[0]
        identifier = existing_work["identifier"]
        query = cequery.work.transform_data_update_composition(identifier, work)
        resp = connection.submit_query(query)
        music_composition = resp["data"]["UpdateMusicComposition"]
    else:
        raise Exception("Unexpectedly got more than 1 entry for a given source")

    work_identifier = music_composition["identifier"]
    logger.info("  work id %s", work_identifier)

    composer = _get_composer_data(work, artist_data)
    composer_identifer = import_or_update_composer(composer)
    join_work_composer(work_identifier, composer_identifer)

    add_documents(work_identifier, work)


def main(data_file=None, artist_file=None, limit=None):
    logger.info("connected to %s", connection.config["import"]["server"])

    with open(data_file) as fp:
        data = json.load(fp)
    with open(artist_file) as fp:
        artist_data = json.load(fp)

    keys = list(data.keys())
    if limit:
        keys = keys[:limit]
    for k in keys:
        work = data[k]
        import_or_update_work(work, artist_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, help='Work data file')
    parser.add_argument('--artist', required=True, help='Artist/composer data file')
    parser.add_argument('--limit', type=int, required=False, help='Only import this many works')

    args = parser.parse_args()
    main(args.data, args.artist, args.limit)

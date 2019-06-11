import argparse
import json
import logging

import musicbrainzngs as mb

from cequery.connection import submit_query
from cequery import transform_works, connection

mb.set_useragent('TROMPA', '0.1')
logger = logging.getLogger('corpus_import')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


def import_work_if_absent(work):
    source = work["Source"]
    title = work["Title"]
    logger.info("Adding work: %s", title)
    existing_work = connection.get_music_composition_by_source(source)
    if len(existing_work) == 0:
        query = transform_works.transform_data_composition(work)
        submit_query(query)
        logger.info(" done")
    else:
        logger.info(" already exists, skipping")


def import_cpdl(cpdl_file):
    with open(cpdl_file) as fp:
        data = json.load(fp)

    for k, work in data.items():
        import_work_if_absent(work)


def import_imslp(imslp_file):
    with open(imslp_file) as fp:
        data = json.load(fp)

    for k, work in data.items():
        import_work_if_absent(work)


def main(imslp_file=None, cpdl_file=None):
    if imslp_file:
        import_imslp(imslp_file)
    elif cpdl_file:
        import_cpdl(cpdl_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--imslp', required=False, help='IMSLP data file')
    group.add_argument('--cpdl', required=False, help='CPDL data file')

    args = parser.parse_args()
    main(args.imslp, args.cpdl)

import argparse

import musicbrainzngs as mb

from cequery.connection import submit_query
from cequery import transform_musicbrainz

mb.set_useragent('TROMPA', '0.1')


def transform_mb_artist_to_gql(artist):
    pass


def transform_mb_work_to_gql(work):
    pass


def import_artist(artist_mbid):
    artist = mb.get_artist_by_id(artist_mbid, includes=["url-rels"])["artist"]
    query = transform_musicbrainz.transform_musicbrainz_artist(artist)
    submit_query(query)


def import_work(work_mbid):
    work = mb.get_artist_by_id(work_mbid, includes=["url-rels"])["work"]
    query = transform_musicbrainz.transform_work(work)
    print(work)
    submit_query(query)


def main(artist_mbid=None, work_mbid=None):
    if artist_mbid:
        import_artist(artist_mbid)
    elif work_mbid:
        import_work(work_mbid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--artist', '-a', required=False, help='Artist MBID to import')
    group.add_argument('--work', '-w', required=False, help='Work MBID to import')

    args = parser.parse_args()
    main(args.artist, args.work)

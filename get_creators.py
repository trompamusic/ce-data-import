import argparse
import json

import musicbrainzngs as mb
mb.set_useragent('TROMPA', '0.1')


def lookup_artists(artists):
    for a in artists:
        print(a)
        lookup_composer(a)


def lookup_composer(composer):
    work = mb.search_artists(artist=composer)
    print(work)


def process_file(fname):
    artists = set()
    with open(fname) as fp:
        data = json.load(fp)
    for k, work in data.items():
        composer = work["Creator"]
        if not composer:
            print(work)
        else:
            artists.add(composer)
    return artists


def main(inputfiles):
    artists = set()
    for f in inputfiles:
        file_artists = process_file(f)
        artists.update(file_artists)

    print("processing %s artists" % len(artists))
    lookup_artists(list(artists))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', nargs='+', help='Json data files to import')

    args = parser.parse_args()
    main(args.inputfile)

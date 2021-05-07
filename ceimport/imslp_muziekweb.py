import os

import click
import csv

import muziekweb_api
from trompace import config

import importers
from ceimport.loader import load_musiccomposition_from_imslp_name, link_musiccomposition_exactmatch
from importers.work import import_work


def auth():
    if 'MUZIEKWEB_USER' not in os.environ or 'MUZIEKWEB_PASS' not in os.environ:
        raise ValueError("Require MUZIEKWEB_USER and MUZIEKWEB_PASS environment variables")
    muziekweb_api.set_api_account(os.environ['MUZIEKWEB_USER'], os.environ['MUZIEKWEB_PASS'])
    config.config.load()


def import_link(item):
    imslp = item['imslp']
    # Go from url to page name
    imslp = imslp.replace("https://imslp.org/wiki/", "").replace("_", " ")
    mw = item['mw']

    mw_id = import_work(mw)
    imslp_id = load_musiccomposition_from_imslp_name(imslp, False)
    link_musiccomposition_exactmatch([mw_id, imslp_id])


@click.group()
def cli():
    pass


@cli.command("import-artist")
@click.argument('artistid')
def import_artist_command(artistid):
    auth()
    a_id = importers.import_artist(artistid)
    print(a_id)


@cli.command("import-work")
@click.argument('workid')
def import_work_command(workid):
    auth()
    w_id = import_work(workid)
    print(w_id)


@cli.command("import")
@click.argument('datafile')
def import_data(datafile):
    auth()
    data = []
    with open(datafile) as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            if line['match_score'] == "100":
                data.append({'mw': line['uniform_title_id'], 'imslp': line['imslp_link']})

    for item in data:
        import_link(item)


if __name__ == '__main__':
    cli()
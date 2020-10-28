import click

from ceimport import loader
from ceimport.sites import imslp


@click.group()
def cli():
    pass


@cli.command()
@click.argument('mbid')
def import_artist_musicbrainz(mbid):
    loader.load_artist_from_musicbrainz(mbid)


@cli.command()
@click.argument('url')
def import_artist_imslp(url):
    loader.load_artist_from_imslp(url)


@cli.command()
@click.argument('mbid')
def import_work_musicbrainz(mbid):
    click.echo('Import work')
    loader.load_musiccomposition_from_musicbrainz(mbid)


@cli.command()
@click.option('--file')
@click.option('--url')
def import_work_imslp(file, url):
    if url:
        loader.load_musiccomposition_from_imslp(url)
    elif file:
        with open(file, 'r') as fp:
            for page in fp:
                if not page.startswith("https://imslp.org/wiki/"):
                    page = "https://imslp.org/wiki/" + page
                loader.load_musiccomposition_from_imslp(page)


@cli.command()
@click.argument('category_name')
def imslp_pages_in_category(category_name):
    pages = imslp.category_pagelist(category_name)
    for p in pages:
        print(p)


if __name__ == '__main__':
    cli()

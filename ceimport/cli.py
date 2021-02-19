import click

from ceimport import loader
from ceimport.sites import imslp


@click.group()
def cli():
    pass


@cli.command()
@click.argument('category')
def cpdl_import_composers_in_category(category):
    """Find all compositions in a category that have musicxml files and import their composers"""
    loader.import_cpdl_composers_for_category(category)


@cli.command()
@click.argument('category')
def cpdl_import_works_in_category(category):
    """Find all compositions in a category that have musicxml files and import them"""
    loader.import_cpdl_works_for_category(category)


@cli.command()
@click.argument('composer_name')
def cpdl_import_composer(composer_name):
    """Import the given composer"""
    loader.import_cpdl_composer(composer_name)


@cli.command()
@click.argument('work_name')
def cpdl_import_work(work_name):
    """Import the given work"""
    loader.import_cpdl_work(work_name)


@cli.command()
@click.argument('mbid')
def musicbrainz_import_artist(mbid):
    persons = loader.load_artist_from_musicbrainz(mbid)
    loader.create_persons_and_link(persons)


@cli.command()
@click.argument('mbid')
def musicbrainz_import_work(mbid):
    loader.load_musiccomposition_from_musicbrainz(mbid)


@cli.command()
@click.option('--file')
@click.option('--url')
def imslp_import_artist(file, url):
    """Import an artist category (--url x) or file of artists (--file f)"""
    if url:
        persons = loader.load_artist_from_imslp(url)
        loader.create_persons_and_link(persons)
    elif file:
        with open(file, 'r') as fp:
            for artist in fp:
                persons = loader.load_artist_from_imslp(artist.strip())
                loader.create_persons_and_link(persons)
    else:
        click.echo("Need to provide --url or --file")


@cli.command()
@click.option('--file')
@click.option('--url')
def imslp_import_work(file, url):
    """Import either a work title (--url) or all titles in a file (--file)"""
    if url:
        loader.load_musiccomposition_from_imslp_name(url)
    elif file:
        with open(file, 'r') as fp:
            works = fp.read().splitlines()
            for work in works:
                loader.load_musiccomposition_from_imslp_name(work)
    else:
        click.echo("Need to provide --url or --file")


@cli.command()
@click.argument('reverselookup')
def imslp_import_single_file(reverselookup):
    """Import a specific file, its work, and composition"""

    loader.load_musiccomposition_from_imslp_by_file(reverselookup)


@cli.command()
@click.argument('category')
def imslp_import_works_in_category(category):
    """Import all works in a category if they have musicxml files"""
    pages = imslp.category_pagelist(category)
    for p in pages:
        loader.load_musiccomposition_from_imslp_name(p)


@cli.command()
@click.argument('category_name')
def imslp_pages_in_category(category_name):
    """Print all work pages in a category (e.g. For unaccompanied chorus)"""
    pages = imslp.category_pagelist(category_name)
    for p in pages:
        print(p)


@cli.command()
@click.argument('pages', type=click.File('r'))
def imslp_filter_xml(pages):
    """Given a file containing work pages, filter only the ones that have musicxml files"""
    works = pages.read().splitlines()
    for xml_work in imslp.filter_works_for_xml(works):
        print(xml_work)


if __name__ == '__main__':
    cli()

import click

import ceimport
from ceimport import loader
from ceimport.sites import imslp


@click.group()
def cli():
    pass


@cli.command()
@click.argument('category')
def import_composers_cpdl(category):
    """Find all compositions in a category that have musicxml files and import their composers"""
    loader.import_cpdl_composers_for_category(category)


@cli.command()
@click.argument('category')
def import_works_cpdl(category):
    """Find all compositions in a category that have musicxml files and import them"""
    loader.import_cpdl_works_for_category(category)


@cli.command()
@click.argument('mbid')
def import_artist_musicbrainz(mbid):
    persons = loader.load_artist_from_musicbrainz(mbid)
    loader.create_persons_and_link(persons)


@cli.command()
@click.option('--file')
@click.option('--url')
def import_artist_imslp(file, url):
    if url:
        persons = loader.load_artist_from_imslp(url)
        loader.create_persons_and_link(persons)
    elif file:
        with open(file, 'r') as fp:
            for artist in fp:
                persons = loader.load_artist_from_imslp(artist.strip())
                loader.create_persons_and_link(persons)


@cli.command()
@click.argument('mbid')
def import_work_musicbrainz(mbid):
    loader.load_musiccomposition_from_musicbrainz(mbid)


@cli.command()
@click.option('--file')
@click.option('--url')
@click.option('--need-xml/--no-need-xml', is_flag=True, default=True, help="If set, require that there is an xml file for download")
def import_work_imslp(file, url, need_xml):
    if url:
        loader.load_musiccomposition_from_imslp_url(url, need_xml)
    elif file:
        with open(file, 'r') as fp:
            works = fp.read().splitlines()
            for work in works:
                loader.load_musiccomposition_from_imslp(work, need_xml=True)


@cli.command()
@click.argument('category_name')
def imslp_pages_in_category(category_name):
    """For unaccompanied chorus"""
    pages = imslp.category_pagelist(category_name)
    for p in pages:
        print(p)


@cli.command()
@click.argument('pages', type=click.File('r'))
def imslp_filter_xml(pages):
    works = pages.read().splitlines()
    for xml_work in imslp.filter_works_for_xml(works):
        print(xml_work)


@cli.command()
def clear_cache():
    ceimport.cache.delete_cache()


if __name__ == '__main__':
    cli()

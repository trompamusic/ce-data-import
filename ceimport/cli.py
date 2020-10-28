import click

from ceimport import loader


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


if __name__ == '__main__':
    cli()

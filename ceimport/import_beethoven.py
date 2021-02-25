"""
Import data representing MEI encodings of Beethoven piano works.

The input should be a json file containing a list of dictionaries of the following form:

  {
    "imslp": "https://imslp.org/wiki/Special:ReverseLookup/52946",
    "mediaobject": {
      "contributor": "https://iwk.mdw.ac.at",
      "source": "https://github.com/trompamusic-encodings/Beethoven_Op35_BreitkopfHaertel/blob/master/Beethoven_Op35.mei",
      "title": "Beethoven_Op35_BreitkopfHaertel/Beethoven_Op35.mei at master \u00b7 trompamusic-encodings/Beethoven_Op35_BreitkopfHaertel",
      "format_": "text/html",
      "name": "Beethoven_Op35.mei",
      "url": "https://github.com/trompamusic-encodings/Beethoven_Op35_BreitkopfHaertel",
      "contenturl": "https://raw.githubusercontent.com/trompamusic-encodings/Beethoven_Op35_BreitkopfHaertel/master/Beethoven_Op35.mei",
      "encodingformat": "application/mei+xml"
    }
  },
"""

import json

import click

from ceimport import loader


def import_single_beethoven(row):
    imslp_reverse_url = row["imslp"]
    musiccomposition = loader.load_musiccomposition_from_imslp_by_file(imslp_reverse_url)

    beethoven_mo = row["mediaobject"]
    beethoven_mo["license"] = "CC-BY 4.0"
    xmlmediaobject_ceid = loader.get_or_create_mediaobject(beethoven_mo)
    loader.link_musiccomposition_and_mediaobject(composition_id=musiccomposition,
                                                 mediaobject_id=xmlmediaobject_ceid)


@click.group()
def cli():
    pass


@cli.command("import")
@click.argument('datafile')
def import_data(datafile):
    with open(datafile) as fp:
        data = json.load(fp)

    for item in data:
        import_single_beethoven(item)

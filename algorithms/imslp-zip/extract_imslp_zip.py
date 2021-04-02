import base64
import hashlib
import io
import zipfile

import click
import requests
import trompace.mutations.mediaobject
import trompace.queries.mediaobject
import trompace.connection
import trompace.config


CONTRIBUTOR_IMSLP = "https://imslp.org"


def imslp_file_url_to_download_url(file_url):
    """Take a MediaWiki File: page (e.g. File:PMLP129863-HandAbO.zip)
    and use the mediawiki api to get the actual URL of the file"""

    params = {"action": "query",
              "prop": "imageinfo",
              "titles": file_url,
              "format": "json",
              "iiprop": "url"}
    url = 'https://imslp.org/api.php'

    r = requests.get(url, params=params)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        return []

    pages = j['query']['pages']
    for k, v in pages.items():
        info = v.get('imageinfo')
        if info:
            if file_url in info[0]["descriptionurl"]:
                return "https:" + info[0]["url"]


def download_imslp_url(download_url):
    cookie = {"imslpdisclaimeraccepted": "yes"}
    r = requests.get(download_url, cookies=cookie)
    return r.content


def extract_imslp_zip(mediaobject_id):
    # Get mediaobject from CE, check it's from imslp, and that it has no contentUrl
    return_items = ["name", "contributor", "url", "contentUrl"]
    query = trompace.queries.mediaobject.query_mediaobject(identifier=mediaobject_id, return_items=return_items)
    resp = trompace.connection.submit_query(query)
    mediaobject = resp.get("data", {}).get("MediaObject", [])
    if mediaobject:
        mediaobject = mediaobject[0]
    else:
        print("Cannot find a MediaObject, skipping")
        return

    name = mediaobject["name"]
    print(f"Processing: {name}")

    contenturl = mediaobject["contentUrl"]
    if contenturl:
        print("contentUrl is already set, skipping")
        return

    contributor = mediaobject["contributor"]
    if contributor != CONTRIBUTOR_IMSLP:
        print("Contributor isn't IMSLP, skipping")
        return

    if not name.lower().endswith(".zip"):
        print("File doesn't appear to be a zip, skipping")
        return

    downloadurl = imslp_file_url_to_download_url(name)
    if not downloadurl:
        print("Could not find download url from the name")
        return

    # TODO: Compressed .mxl file
    zip_contents = download_imslp_url(downloadurl)
    zipfp = io.BytesIO(zip_contents)
    try:
        with zipfile.ZipFile(zipfp, "r") as zip:
            xml_name = [f for f in zip.namelist() if f.lower().endswith(".xml")]
    except zipfile.BadZipFile:
        print("Contents doesn't appear to be a zip file")
        return

    if len(xml_name) == 0:
        print("Could not find any xml files")
        return

    if len(xml_name) > 1:
        print("Got more than 1 xml file: ", xml_name)
        return

    # https://s11.no/2018/arcp.html#hash-based
    xml_name = xml_name[0]
    file_contents_sha256 = hashlib.sha256(zip_contents).hexdigest()
    file_contents_b64 = base64.b64encode(file_contents_sha256.encode("ascii")).decode("ascii")
    # Get sha256 of the file
    contenturl = "arcp://ni,sha-256;" + file_contents_b64 + "/" + xml_name

    # Update object
    mutation = trompace.mutations.mediaobject.mutation_update_media_object(
        identifier=mediaobject_id,
        contenturl=contenturl,
        encodingformat="application/vnd.recordare.musicxml+xml"
    )
    trompace.connection.submit_query(mutation, auth_required=True)


@click.group()
def cli():
    pass


@cli.command("extract-imslp-zip")
@click.argument("mediaobject_id")
def extract_imslp_zip_command(mediaobject_id):
    """Given a MediaObject, add an arcp url to contentUrl based on the location of a musicxml file inside a zip archive"""
    "f1d4af18-0e4e-4ebf-9f76-3052a024fe8c"
    extract_imslp_zip(mediaobject_id)


if __name__ == '__main__':
    trompace.config.config.load()
    cli()

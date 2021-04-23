"""
Given a MediaObject node that refers to a musixml file (from cpdl or imslp), download it,
convert it to mei using verovio, and create a new MediaObject node

If the file is an imslp zip, the musicxml file is extracted first. If the file is a .mxl
(compressed zip), the .xml file inside the zip is extracted.

The new node is linked to the work (exampleOfWork), and the musicxml file (derivedFrom)

TODO: we assume that the basename of all files is unique. Should we use a uuid instead? or a prefix
TODO: Need to check that the file doesn't already exist before creating it
TODO: Duplicate imslp access methods in other algorithms. Can these be factored out?
"""

import io
import os
import subprocess
import sys
import tempfile
import zipfile
from typing import Tuple
from urllib.parse import urlparse, urlunparse

import boto3
import click
import requests
from trompace.config import config
from trompace.connection import submit_query
from trompace.mutations import mediaobject
import trompace.mutations.application as mutations_application
import trompace.queries.application as queries_application
from trompace.queries.mediaobject import query_mediaobject


config.load()

ACCESS_KEY = os.environ['S3_ACCESS_KEY']
SECRET_KEY = os.environ['S3_SECRET_KEY']
S3_HOST = os.environ['S3_HOST']
S3_BUCKET = 'meiconversion'
# This is an s3 policy for a bucket called 'meiconversion' that allows anyone to download items from it
S3_POLICY = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetBucketLocation","s3:ListBucket"],"Resource":["arn:aws:s3:::meiconversion"]},{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::meiconversion/*"]}]}'


class FailedToConvertXml(Exception):
    pass


def get_or_create_musescore_application():
    creator = "https://github.com/trompamusic/ce-data-import/tree/master/algorithms/mxml-to-mei"
    source = "https://musescore.org"

    run = subprocess.run(
        ['mscore3', '-v', '-platform', 'offscreen'],
        env={'XDG_RUNTIME_DIR': '/tmp'},
        check=True,
        capture_output=True
    )
    version = str(run.stdout, "utf-8").strip()

    query_application = queries_application.query_softwareapplication(
        creator=creator,
        source=source,
        softwareversion=version
    )
    app_response = submit_query(query_application, auth_required=True)
    app = app_response.get('data', {}).get('SoftwareApplication', [])
    if app:
        return app[0]["identifier"]
    else:
        mutation_create = mutations_application.mutation_create_application(
            name="Musescore",
            contributor=source,
            creator=creator,
            source=source,
            language="en",
            title="Musescore",
            softwareversion=version
        )
        create_response = submit_query(mutation_create, auth_required=True)
        app = create_response.get('data', {}).get('CreateSoftwareApplication', {})
        return app["identifier"]


def get_or_create_verovio_application():
    creator = "https://github.com/trompamusic/ce-data-import/tree/master/algorithms/mxml-to-mei"
    source = "https://www.verovio.org"

    run = subprocess.run(
        ['verovio', '-v'],
        check=True,
        capture_output=True
    )
    version = str(run.stdout, "utf-8").strip()

    query_application = queries_application.query_softwareapplication(
        creator=creator,
        source=source,
        softwareversion=version
    )
    app_response = submit_query(query_application, auth_required=True)
    app = app_response.get('data', {}).get('SoftwareApplication', [])
    if app:
        return app[0]["identifier"]
    else:
        mutation_create = mutations_application.mutation_create_application(
            name="Verovio",
            contributor=source,
            creator=creator,
            source=source,
            language="en",
            title="Verovio",
            softwareversion=version
        )
        create_response = submit_query(mutation_create, auth_required=True)
        app = create_response.get('data', {}).get('CreateSoftwareApplication', {})
        return app["identifier"]


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


def get_file_in_imslp_archive(download_url, arcpurl):
    """Given a download url for imslp (from `imslp_file_url_to_download_url`), download
    the zip at the location, and uncompress the file defined by arcpurl"""
    # TODO: Doesn't check the hash of arcpurl
    cookie = {"imslpdisclaimeraccepted": "yes"}
    r = requests.get(download_url, cookies=cookie)
    zipfp = io.BytesIO(r.content)
    filename = os.path.basename(arcpurl)
    try:
        with zipfile.ZipFile(zipfp, "r") as zip:
            with zip.open(filename, "r") as fp:
                return fp.read().decode("utf-8")
    except zipfile.BadZipFile:
        print("Contents doesn't appear to be a zip file")
        return


def uncompress_mxl_to_xml(mxl_file):
    """an mxl is a zip file that contains a manifest and the actual xml file."""
    with zipfile.ZipFile(mxl_file) as zipfp:
        names = zipfp.namelist()
        xmlnames = [n for n in names if "/" not in n and n.lower().endswith(".xml")]
        if len(xmlnames) == 0:
            raise ValueError("Cannot find any xml file")
        elif len(xmlnames) > 1:
            raise ValueError("Found more than one xml in the root?")
        else:
            return zipfp.read(xmlnames[0]).decode("utf-8")


def convert_mxml_to_mei_file(inputdata, inputname) -> Tuple[str, bool]:
    """
    returns a tuple  meidata, used_musescore
    used_musescore is True if it had to convert with musescore first
    """
    if inputname.endswith(".mxl"):
        data = uncompress_mxl_to_xml(inputdata)
    else:
        data = inputdata

    with tempfile.TemporaryDirectory() as tmpdir:
        outputname = os.path.join(tmpdir, "output.mei")
        inputname = os.path.join(tmpdir, "input.xml")
        with open(inputname, "w") as fp:
            fp.write(data)
        try:
            return run_mxml_to_mei_verovio(inputname, outputname), False
        except subprocess.CalledProcessError:
            # Vervio failed to run, for example it could have segfaulted! In this case, convert
            # the file using musescore, from mxml to mxml and try again
            print("failed to convert with verovio, trying again")
            try:
                new_mxml = run_mxml_to_mxml_musescore(inputname, tmpdir)
                return run_mxml_to_mei_verovio(new_mxml, outputname), True
            except subprocess.CalledProcessError as e:
                print(e)
                # Still got a problem... give up
                raise FailedToConvertXml(e)


def run_mxml_to_mei_verovio(inputname, outputname):
    run = subprocess.run(
        ['verovio', '-a', '-f', 'xml', '-t', 'mei', '-o', outputname, inputname],
        check=True,
        capture_output=True
    )
    return open(outputname).read()


def run_mxml_to_mxml_musescore(inputname, tmpdir):
    musescore_output = os.path.join(tmpdir, "musescore_output.musicxml")
    run = subprocess.run(
        ['mscore3', inputname, '-o', musescore_output, '-platform', 'offscreen'],
        check=True,
        capture_output=True,
        env={'XDG_RUNTIME_DIR': '/tmp'}
    )
    return musescore_output


def upload_mei_to_s3(meidata, filename):
    client = boto3.client(
        's3',
        endpoint_url=S3_HOST,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    try:
        client.create_bucket(Bucket=S3_BUCKET)
        client.put_bucket_policy(Policy=S3_POLICY, Bucket=S3_BUCKET)
    except client.exceptions.BucketAlreadyOwnedByYou:
        pass
    client.upload_fileobj(meidata, S3_BUCKET, filename)

    file_path = os.path.join(S3_BUCKET, filename)
    host_parsed = list(urlparse(S3_HOST))
    host_parsed[2] = file_path

    return urlunparse(host_parsed)


def create_blank_mei_node():
    """Create a MediaObject that we want to use to store an MEI file, but
    don't add any content to it. This is so that we can get the identifier to name the file
    in the local filesystem."""
    imslp_mei = mediaobject.mutation_create_media_object(
        creator="https://github.com/trompamusic/ce-data-import/tree/master/algorithms/mxml-to-mei",
        # Who this data came from
        contributor="https://trompamusic.eu",
        # These values must be set, but we'll update them later in update_mei_node
        title="",
        source="",
        format_="/"
    )
    mei_response = submit_query(imslp_mei, auth_required=True)
    mei = mei_response.get('data', {}).get('CreateMediaObject', {})
    if mei:
        return mei["identifier"]
    else:
        return None


def create_mei_node(meiurl):
    filename = os.path.basename(meiurl)

    imslp_mei = mediaobject.mutation_create_media_object(
        creator="https://github.com/trompamusic/ce-data-import/tree/master/algorithms/mxml-to-mei",
        # Who this data came from
        contributor="https://trompamusic.eu",
        # URL on the web that matches contentUrl
        source=meiurl,
        # The <title> of `source`
        title=filename,
        # The mimetype of `source`
        format_="application/mei+xml",
        name=filename,
        # The page that describes the resource
        url=meiurl,
        contenturl=meiurl,
        encodingformat="application/mei+xml"
    )
    mei_response = submit_query(imslp_mei, auth_required=True)
    mei = mei_response.get('data', {}).get('CreateMediaObject', {})
    if mei:
        return mei["identifier"]
    else:
        return None


def update_mei_node(mei_id, meiurl):
    filename = os.path.basename(meiurl)

    """Given an MEI MediaObject node id, update it to add the URL """
    imslp_mei = mediaobject.mutation_update_media_object(
        identifier=mei_id,
        # URL on the web that matches contentUrl
        source=meiurl,
        # The <title> of `source`
        title=filename,
        # The mimetype of `source`
        format_="application/mei+xml",
        name=filename,
        # The page that describes the resource
        url=meiurl,
        contenturl=meiurl,
        encodingformat="application/mei+xml"
    )
    mei_response = submit_query(imslp_mei, auth_required=True)
    mei = mei_response.get('data', {}).get('UpdateMediaObject', {})
    if mei:
        return mei["identifier"]
    else:
        return None


def join_existing_and_new_mei(musiccomposition_id, mxml_mo_id, mei_mo_id, used_musescore: bool):
    """
    Indicate that the MEI is an exampleOfWork of the composition
    That the MEI wasDerivedFrom the MXML
    That the MEI used verovio to create it
    """

    application_id = get_or_create_verovio_application()
    example_mutation = mediaobject.mutation_merge_mediaobject_example_of_work(mei_mo_id, work_identifier=musiccomposition_id)
    submit_query(example_mutation, auth_required=True)
    derivedfrom_mutation = mediaobject.mutation_merge_media_object_wasderivedfrom(mei_mo_id, mxml_mo_id)
    submit_query(derivedfrom_mutation, auth_required=True)
    used_mutation = mediaobject.mutation_add_media_object_used(mei_mo_id, application_id)
    submit_query(used_mutation, auth_required=True)
    if used_musescore:
        musescore_application_id = get_or_create_musescore_application()
        used_mutation = mediaobject.mutation_add_media_object_used(mei_mo_id, musescore_application_id)
        submit_query(used_mutation, auth_required=True)


def mei_for_xml_exists(mediaobject_id):
    mo_query = query_mediaobject(
        filter_={"wasDerivedFrom": {"identifier": mediaobject_id}, "format": "application/mei+xml"})
    mo_response = submit_query(mo_query)
    mo = mo_response.get('data', {}).get('MediaObject', [])
    if mo:
        return True
    else:
        return False


def process_cpdl(mediaobject):
    mo_contenturl = mediaobject['contentUrl']

    mei_mo_id = create_blank_mei_node()
    mei_filename = mei_mo_id + ".mei"

    r = requests.get(mo_contenturl)
    file_content = io.BytesIO(r.content)

    try:
        mei_content, used_musescore = convert_mxml_to_mei_file(file_content, mo_contenturl)

        mei_fp = io.BytesIO(mei_content.encode("utf-8"))
        mei_url = upload_mei_to_s3(mei_fp, mei_filename)

        update_mei_node(mei_mo_id, mei_url)

        return mei_mo_id, used_musescore
    except FailedToConvertXml:
        pass


def process_imslp(mediaobject):
    mo_contenturl = mediaobject['contentUrl']
    mei_mo_id = create_blank_mei_node()
    mei_filename = mei_mo_id + ".mei"

    download_url = imslp_file_url_to_download_url(mediaobject['name'])
    mxml_file = get_file_in_imslp_archive(download_url, mo_contenturl)

    try:
        mei_content, used_musescore = convert_mxml_to_mei_file(mxml_file, mo_contenturl)

        mei_fp = io.BytesIO(mei_content.encode("utf-8"))
        mei_url = upload_mei_to_s3(mei_fp, mei_filename)
        update_mei_node(mei_mo_id, mei_url)

        return mei_mo_id, used_musescore
    except FailedToConvertXml:
        pass


def convert_ce_node(mediaobject_id):
    """Take a MediaObject
    Ensure that encodingFormat is one of the musicxml ones
    - if the contenturl is a content url, then find it (special-case imslp), otherwise just download it
    - do conversion
    - create mediaobject, link to input file, link to composition, upload to s3"""

    if mei_for_xml_exists(mediaobject_id):
        print("An MEI file derived from this MusicXML already exists", file=sys.stderr)
        return

    return_items = ["identifier", "name", "contributor", "url", "contentUrl", {"exampleOfWork": ["identifier"]}]
    mo_query = query_mediaobject(identifier=mediaobject_id, return_items=return_items)
    mo_response = submit_query(mo_query)
    mo = mo_response.get('data', {}).get('MediaObject', [])
    if mo:
        mo = mo[0]
        mo_id = mo['identifier']
        mo_contributor = mo['contributor']
        work = mo['exampleOfWork']
        if not work:
            print('Unexpectedly this MediaObject has no exampleOfWork', file=sys.stderr)
            return
        work_id = work[0]['identifier']

        if mo_contributor == "https://cpdl.org":
            mei_id, used_musescore = process_cpdl(mo)
        elif mo_contributor == "https://imslp.org":
            mei_id, used_musescore = process_imslp(mo)
        else:
            print("Contributor isn't one of cpdl or imslp", file=sys.stderr)
            return
        join_existing_and_new_mei(musiccomposition_id=work_id,
                                  mxml_mo_id=mo_id, mei_mo_id=mei_id,
                                  used_musescore=used_musescore)
    else:
        print("Cannot find a MediaObject", file=sys.stderr)
        return


@click.group()
def cli():
    pass


@cli.command("convert-mxml-to-mei-node")
@click.argument("mediaobject_id")
def convert_mxml_to_mei_node_command(mediaobject_id):
    """0c297551-6a77-47a5-aa18-b8b114d64691"""
    convert_ce_node(mediaobject_id)


@cli.command("convert-mxml-to-mei-file")
@click.argument("inputpath")
@click.argument("outputpath")
def convert_mxml_to_mei_file_command(inputpath, outputpath):
    convert_mxml_to_mei_file(inputpath, outputpath)


if __name__ == '__main__':
    cli()

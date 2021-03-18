import os
import tempfile
import zipfile

import click
import verovio


def uncompress_mxl_to_xml(mxl_file):
    """an mxl is a zip file that contains a manifest and the actual xml file."""
    with zipfile.ZipFile(mxl_file) as zipfp:
        names = zipfp.namelist()
        xmlnames = [n for n in names if "/" not in n]
        if len(xmlnames) == 0:
            raise ValueError("Cannot find any xml file")
        elif len(xmlnames) > 1:
            raise ValueError("Found more than one xml in the root?")
        else:
            return zipfp.read(xmlnames[0]).decode("utf-8")


def convert_mxml_to_mei_file(inputpath, outputpath):
    # TODO: If it's compressed, need to undo it (current version of verovio doesn't support mxl)

    if inputpath.endswith(".mxl"):
        data = uncompress_mxl_to_xml(inputpath)
    else:
        with open(inputpath) as fp:
            data = fp.read()

    tk = verovio.toolkit()
    tk.loadData(data)
    mei = tk.getMEI({})
    with open(outputpath, "w") as fp:
        fp.write(mei)


def upload_mei_to_s3(meifile):

    pass


def create_mei_node(meipath, mediaobject_id, musiccomposition_id):
    filename = os.path.basename(meipath)

    # TODO: Should source, url, _and_ contentUrl be the url to the file?
    imslp_mei = mediaobject.mutation_create_media_object(
        creator="https://github.com/trompamusic/trompa-ce-client/tree/master",
        # Who this data came from
        contributor="https://trompamusic.eu",
        # URL on the web that matches contentUrl
        source=meipath,
        # The <title> of `source`
        title=filename,
        # The mimetype of `source`
        format_="application/mei+xml",
        name=filename,
        # The page that describes the resource
        url=meipath,
        contenturl=meipath,
        encodingformat="application/mei+xml"
    )

    """
    # All of the MediaObjects are examples of the MusicComposition
    example_of_work_pdf = mediaobject.mutation_merge_mediaobject_example_of_work(pdf_id, work_identifier=work_id)
    # In the case of CPDL, we know that scores are written in an editor and then rendered to PDF.
    # Therefore, the PDF wasDerivedFrom the xml (http://www.w3.org/ns/prov#wasDerivedFrom)
    pdf_derived_from_xml = mediaobject.mutation_merge_media_object_wasderivedfrom(pdf_id, xml_id)

    application created by:
    mutation_add_actioninterface_result
    """


def find_imslp_download_url(imslp_file):
    pass


def convert_ce_node(mediaobject_id, temporary_dir):
    """Take a MediaObject
    Ensure that encodingFormat is one of the musicxml ones
    - if the contenturl is a content url, then find it (special-case imslp), otherwise just download it
    - do conversion
    - create mediaobject, link to input file, link to composition, upload to s3"""


@click.group()
def cli():
    pass


@cli.command("convert-mxml-to-mei-node")
@click.argument("mediaobject_id")
def convert_mxml_to_mei_node_command(mediaobject_id):
    """0c297551-6a77-47a5-aa18-b8b114d64691"""
    with tempfile.mkdtemp() as tmpdir:
        convert_ce_node(mediaobject_id, tmpdir)
    pass


@cli.command("convert-mxml-to-mei-file")
@click.argument("inputpath")
@click.argument("outputpath")
def convert_mxml_to_mei_file_command(inputpath, outputpath):
    convert_mxml_to_mei_file(inputpath, outputpath)


if __name__ == '__main__':
    cli()

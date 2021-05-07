import trompace.connection
from trompace.mutations.musiccomposition import mutation_create_music_composition

import muziekweb_api
from ceimport.loader import link_musiccomposition_and_composers
from importers import import_artist
from importers.audio_object import MW_MUSIC_URL
from models import CE_MusicComposition
from trompace_local import GLOBAL_IMPORTER_REPO


def import_work(work_id: str):
    """Import a work from Muziekweb and import it to the CE
    Returns a dictionary:
        {"musiccomposition_id": musiccomp_ceid,
         "person_ids": composer_ids}
    """
    work_meta = get_work(work_id)
    mw_composer = import_artist(work_meta['composer_id'])

    # TODO: this catalogue should be taken from the document. The ending slug should be computed
    source = MW_MUSIC_URL.format(work_id, "CLASSICAL", "")
    work = CE_MusicComposition(
        identifier=None,
        name=work_meta['work_name'],
        url=source,
        contributor='https://www.muziekweb.nl',
        creator=GLOBAL_IMPORTER_REPO,
    )

    create_composition = mutation_create_music_composition(**work.as_dict())
    response = trompace.connection.submit_query(create_composition, auth_required=True)
    work.identifier = response["data"]["CreateMusicComposition"]["identifier"]

    # Join composer and work
    link_musiccomposition_and_composers(work.identifier, [mw_composer.identifier])
    return work.identifier


def get_work(work_id: str):
    """Query muziekweb api and parse result

    TODO: Error detection
          Work parts
          Import multiple languages if present
    """
    work = muziekweb_api.get_work(work_id)
    info = work.getElementsByTagName("UniformTitleInfo")[0]
    name = None
    for title in info.getElementsByTagName("UniformTitle"):
        if title.getAttribute("Language") == "en":
            name = title.firstChild.nodeValue
    if not name:
        raise ValueError("Could not find english name")
    composer_id = None
    composer = info.getElementsByTagName("Performer")[0]
    role = composer.getElementsByTagName("PrimaryRoleCode")[0]
    if role and role.firstChild.nodeValue == "COMPOSER":
        composer_id = composer.getAttribute("Link")

    return {"work_id": work_id,
            "work_name": name,
            "composer_id": composer_id}
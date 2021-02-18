import base64
import json
import random
import re
import sys
import time
import urllib
from typing import List

from bs4 import BeautifulSoup
import requests
import requests_cache
from mediawiki import mediawiki
import mwparserfromhell as mwph
from requests.adapters import HTTPAdapter

from ceimport import chunks


def make_throttle_hook():
    """
    Returns a response hook function which sleeps for `timeout` seconds if
    response is not cached
    """
    def hook(response, *args, **kwargs):
        if not getattr(response, 'from_cache', False):
            print('sleeping')
            time.sleep(random.randint(500, 3000) / 1000.0)
        return response
    return hook


session = requests_cache.CachedSession()
session.hooks = {'response': make_throttle_hook()}
adapter = HTTPAdapter(max_retries=5)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_titles_in_category(mw, category):
    """Get a list of works constrained by the category from the specified URL

    Arguments:
        mw: a MediaWiki object pointing to an API
        category: the category title to get page titles from
    """
    return mw.categorymembers(category, results=None, subcategories=True)[0]


def read_source(source: str) -> str:
    """Read a URL and return the HTML string.

    Args:
        source: the URL of the page to load

    Returns:
        the contents of the page
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = session.get(source, headers=headers)
    try:
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError:
        return None


def get_page_title(source):
    page = read_source(source)
    if page is not None:
        bs = BeautifulSoup(page, features="lxml")
        title = bs.find("title")
        if title:
            return title.text


def special_link_to_download_url(special_link, download_id):
    url = ""
    r = session.get(url, cookies={"imslpdisclaimeraccepted": "yes"}, allow_redirects=False)
    location = r.headers['Location']
    return location


def get_pages_for_category(mw, category_name, page_name=None, num_pages=None):
    print("Getting pages for category {}".format(category_name))
    list_of_titles = get_titles_in_category(mw, category_name)
    if page_name and page_name in list_of_titles:
        return [page_name]
    elif page_name and page_name not in list_of_titles:
        raise Exception("Asked for page '{}' but it's not here".format(page_name))

    if num_pages:
        print("Limiting number of pages to {}".format(num_pages))
        list_of_titles = list_of_titles[:num_pages]

    return list_of_titles


def category_pagelist(category_name: str):
    mw = mediawiki.MediaWiki(url='https://imslp.org/api.php', rate_limit=True)

    list_of_titles = get_pages_for_category(mw, category_name)
    return list_of_titles


def get_wiki_content_for_pages(pages: List[str]):
    """Use the mediawiki api to load Wikitext for a list of page"""
    if len(pages) > 50:
        raise ValueError("can only do up to 50 pages")

    query = "|".join(pages)
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": query,
        "rvslots": "*",
        "rvprop": "content",
        "formatversion": "2",
        "format": "json"
    }
    url = 'https://imslp.org/api.php'

    r = session.get(url, params=params)

    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        return []

    # ["query"]["pages"]["5827"]["revisions"][0]["*"]
    pages = j.get("query", {}).get("pages", {})

    """
    imslp api returns a dictionary where page ids are the key values
      -> this is different to the cpdl one
    """
    ret = []
    for pageid, page in pages.items():
        if pageid == "-1" and "missing" in page:
            # TODO Logging
            pass

        title = page["title"]
        revisions = page.get("revisions")
        if revisions:
            text = revisions[0].get("*")
            ret.append({"title": title, "content": text})

    return ret


def api_all_pages():
    """Get a list of all composition pages in IMSLP, including the category which represents the work's composer"""
    base_url = "https://imslp.org/imslpscripts/API.ISCR.php?account=worklist/disclaimer=accepted/sort=id/type=2/start={}/retformat=json"
    hasnext = True
    start = 0
    alldata = []
    while hasnext:
        url = base_url.format(start)
        print(url)
        r = session.get(url)
        j = r.json()
        metadata = j.get('metadata', {})
        if metadata:
            hasnext = metadata.get('moreresultsavailable', False)
        for i in range(1000):
            data = j.get(str(i))
            if data:
                alldata.append(data)
        start += 1000
    with open("all-imslp-pages.json", "w") as fp:
        json.dump(alldata, fp)


def parse_imslp_date(year, month, day):
    """Return a date from imslp. Only return if all 3 components exist, and are integers
    This prevents parsing items that only have some components (e.g. yyyy-mm), or approximate
    values (e.g. c 1600)"""
    if year and month and day:
        try:
            year = int(year)
            month = int(month)
            day = int(day)
            return f"{year:d}-{month:02d}-{day:02d}"
        except ValueError:
            return None


def imslp_api_raw_query(page_name):
    """Use the custom IMSLP API to get some parsed metadata for a page"""
    page_id = base64.b64encode(urllib.parse.quote(page_name).encode("utf-8"))
    page_id = page_id.decode('utf-8')
    url = f"https://imslp.org/imslpscripts/API.ISCR.php?retformat=json/disclaimer=accepted/type=0/id={page_id}"
    r = session.get(url)
    try:
        return r.json()
    except ValueError:
        print(r.text)
    return {}


def api_composer_get_relations(composer_name):
    j = imslp_api_raw_query(composer_name)
    if "0" not in j:
        return {}

    composer = j["0"]
    intvals = composer["intvals"]
    authorities = intvals.get("wikidata", {}).get("authorities", [])

    external_relations = {}
    for link, url, identifier in authorities:
        if identifier == "Worldcat":
            external_relations['worldcat'] = url
        elif link == "[[wikipedia:Virtual International Authority File|VIAF]]":
            external_relations['viaf'] = url
        elif identifier == "Wikipedia":
            external_relations['wikipedia'] = url
        elif link == "[[wikipedia:MusicBrainz|MusicBrainz]]":
            external_relations['musicbrainz'] = identifier
        elif link == "[[wikipedia:International Standard Name Identifier|ISNI]]":
            external_relations['isni'] = url
        elif link == "[[wikipedia:Library of Congress Control Number|LCCN]]":
            external_relations['loc'] = url

    return external_relations


def api_composer(composer_name):
    """
    Load a composer from ISMLP and return a dictionary adequate to create a Person on the CE
    Arguments:
          composer_name: an imslp Category name for a composer"""
    j = imslp_api_raw_query(composer_name)
    if "0" not in j:
        return None

    composer = j["0"]
    extvals = composer["extvals"]
    intvals = composer["intvals"]
    family_name = intvals.get("lastname")
    given_name = intvals.get("firstname")
    name = intvals.get("normalname")
    gender = extvals.get("Sex")
    image = intvals.get("picturelinkraw")
    if image:
        image = f"https://imslp.org{image}"

    birth_date = parse_imslp_date(extvals.get("Born Year"), extvals.get("Born Month"), extvals.get("Born Day"))
    death_date = parse_imslp_date(extvals.get("Died Year"), extvals.get("Died Month"), extvals.get("Died Day"))

    composer_source = composer["permlink"]

    # Make a second query to get the actual html title
    page = read_source(composer_source)
    if page is not None:
        title = get_page_title(composer_source)

        return {
            'contributor': 'https://imslp.org',
            'source': composer_source,
            'format_': 'text/html',
            'language': 'en',
            'title': title,
            'name': name,
            'gender': gender,
            'family_name': family_name,
            'given_name': given_name,
            'birth_date': birth_date,
            'death_date': death_date,
            'image': image
        }
    else:
        return {}


def api_work(work_name):
    """Load a work from IMSLP and return a dict adequate to load MusicComposition into CE

    There are two places where we can get metadata from:
       - one is the wikitext of the page
       - the other is the IMSLP API for a page, given the base64 of a title
       https://imslp.org/imslpscripts/API.ISCR.php?retformat=json/disclaimer=accepted/type=0/id=VmFyaWF0aW9ucyBhbmQgRnVndWUgaW4gRS1mbGF0IG1ham9yLCBPcC4zNSAoQmVldGhvdmVuLCBMdWR3aWcgdmFuKQ==
    """

    url = "https://imslp.org/wiki/" + work_name.replace(" ", "_")
    html_page = read_source(url)
    api_page = imslp_api_raw_query(work_name)
    api_page = api_page.get('0', {})

    language_mapping = {'english': 'en',
                        'german': 'de',
                        'spanish': 'es',
                        'french': 'fr',
                        'dutch': 'nl',
                        'catalan': 'ca'}

    if html_page is not None:
        title = get_page_title(url)

        inlanguage = None
        language = api_page.get('extvals', {}).get('Language')
        if language:
            inlanguage = language_mapping.get(language.lower())
            if inlanguage is None:
                print(f"No mapping for language {language}")

        name = api_page.get('extvals', {}).get('Work Title')
        composer = api_page.get('parent')

        work_dict = {
            'title': title,
            'name': name,
            'contributor': 'https://imslp.org',
            'source': url,
            'format_': 'text/html',
            'language': 'en',
            'inlanguage': inlanguage
        }
    else:
        work_dict = {}
        composer = ""

    return {"work": work_dict,
            "composer": composer}


def get_mediaobject_for_filename(work_wikitext, filename):
    """
    If we have a specific file that we want to import (looked up from a Special:ReverseLookup)
    then find that file in the provided wikitext and return information to create a MediaObject
    TODO: This shares a lot of common code with `files_for_work`
    """
    # Filename doesn't include File: prefix in the template
    if filename.startswith("File:"):
        filename = filename.replace("File:", "")

    parsed = mwph.parse(work_wikitext["content"])
    # A page should have one node, the #fte:imslppage template
    nodes = parsed.nodes
    assert len(nodes) == 1
    node = nodes[0]

    # One of the parameters in this template is ' *****FILES***** '
    files_param = None
    for param in node.params:
        if param.name == ' *****FILES***** ':
            files_param = param
            break

    if files_param:
        files = files_param.value
        file_node = None
        for node in files.nodes:
            is_file_node = False
            if hasattr(node, 'name') and node.name.strip() == "#fte:imslpfile":
                for fileparam in node.params:
                    if "File Name" in fileparam.name and fileparam.value == filename:
                        is_file_node = True
                    break
            if is_file_node:
                break
        if file_node:
            node_to_dict = {str(n.name): str(n.value).strip() for n in file_node.params}
            chosen_file = [n for n, v in node_to_dict.items() if v == filename]
            file_index = chosen_file[0].replace("File Name ", "")

            license = node_to_dict.get("Copyright")
            title = work_wikitext["title"].replace(" ", "_")
            url = "http://imslp.org/wiki/" + title

            this_file = node_to_dict[f"File Name {file_index}"]
            this_desc = node_to_dict[f"File Description {file_index}"]

            this_file = "File:" + this_file
            permalink = get_permalink_from_filename(title, this_file)
            file_url = "http://imslp.org/wiki/" + this_file
            file_title = get_page_title(file_url)

            # TODO: Person who published, transcribed work. Date of publication on imslp?
            file_dict = {
                'title': file_title,
                'name': this_file,
                'contributor': 'https://imslp.org',
                'source': url,
                'url': permalink,
                'format_': 'text/html',
                'language': 'en',
                'license': license,
                'description': this_desc,
            }
            return file_dict
    return {}


def files_for_work(work_wikitext):
    """Get MediaObject information for files relevant to the work

    If the work has an xml file, get the xml and the pdf associated with it

    Arguments:
        work_wikitext: the result of get_wiki_content_for_pages of a work
    """
    parsed = mwph.parse(work_wikitext["content"])

    # A page should have one node, the #fte:imslppage template
    nodes = parsed.nodes
    assert len(nodes) == 1
    node = nodes[0]

    # One of the parameters in this template is ' *****FILES***** '
    files_param = None
    for param in node.params:
        if param.name == ' *****FILES***** ':
            files_param = param
            break

    # the .value of this parameter is another Wikicode
    if files_param:
        files = files_param.value
        # There are another number of nodes in this Wikicode
        # Some are text, and some are #fte:imslpfile templates
        # We go looking for the #fte:imslpfile template that has an xml file in it,
        # and keep track of the previous node, which should be the title
        last_node = None
        xml_node = None
        for node in files.nodes:
            is_xml_node = False
            if hasattr(node, 'name') and node.name.strip() == "#fte:imslpfile":
                for fileparam in node.params:
                    if "File Description" in fileparam.name and "XML" in fileparam.value:
                        is_xml_node = True
                        break
                if is_xml_node:
                    xml_node = node
                    break
            last_node = node

    else:
        xml_node = last_node = None

    mediaobjects = []
    if xml_node:
        node_to_dict = {str(n.name): str(n.value).strip() for n in xml_node.params}
        num_files = len([n.name for n in xml_node.params if str(n).startswith("File Name")])

        desc_match = re.search("=====(.*)=====", str(last_node))
        if desc_match:
            desc_match = desc_match.group(1)

        license = node_to_dict.get("Copyright")
        title = work_wikitext["title"].replace(" ", "_")
        url = "http://imslp.org/wiki/" + title

        for i in range(1, num_files+1):
            this_file = node_to_dict[f"File Name {i}"]
            this_desc = node_to_dict[f"File Description {i}"]
            if desc_match:
                this_desc = desc_match + ", " + this_desc

            this_file = "File:" + this_file
            permalink = get_permalink_from_filename(title, this_file)
            file_url = "http://imslp.org/wiki/" + this_file
            file_title = get_page_title(file_url)

            # TODO: Person who published, transcribed work. Date of publication on imslp?
            file_dict = {
                'title': file_title,
                'name': this_file,
                'contributor': 'https://imslp.org',
                'source': url,
                'url': permalink,
                'format_': 'text/html',
                'language': 'en',
                'license': license,
                'description': this_desc,
            }
            mediaobjects.append(file_dict)

    return mediaobjects


def get_composition_and_filename_from_permalink(permalink):
    """Given a Special:ReverseLookup url (e.g. https://imslp.org/wiki/Special:ReverseLookup/51109), return
    a tuple of (wiki page, filename) of the filename that this reverse lookup points to
    e.g. (Variations_and_Fugue_in_E-flat_major,_Op.35_(Beethoven,_Ludwig_van), File:PMLP05827-Op.35.pdf)

    Unfortunately there doesn't seem to be a way of getting the permalink file id from the IMSLP or Mediawiki APIs,
    and so we have to do this through html

    """
    if not permalink.startswith("https://imslp.org/wiki/Special:ReverseLookup/"):
        raise ValueError("Permalink must be a reverselookup")

    # We don't use read_source because we need the response object to get the URL from
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = session.get(permalink, headers=headers)
    redirected_url = r.url
    page_name = redirected_url.replace("https://imslp.org/wiki/", "")

    file_id = permalink.replace("https://imslp.org/wiki/Special:ReverseLookup/", "")

    bs = BeautifulSoup(r.text, features="lxml")
    file_href = bs.find("div", {"id": "IMSLP" + file_id}).find("a", string="#" + file_id).attrs["title"]

    return page_name, file_href


def get_permalink_from_filename(wikipage, filename):
    """Given a wiki page title and a filename
    (e.g. Variations_and_Fugue_in_E-flat_major,_Op.35_(Beethoven,_Ludwig_van), File:PMLP05827-Op.35.pdf)
    find the imslp reverse lookup of the file on that page (e.g. https://imslp.org/wiki/Special:ReverseLookup/51109)

    Unfortunately there doesn't seem to be a way of getting the permalink file id from the IMSLP or Mediawiki APIs,
    and so we have to do this through html
    """

    url = "https://imslp.org/wiki/" + wikipage

    # We don't use read_source because we need the response object to get the URL from
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = session.get(url, headers=headers)
    bs = BeautifulSoup(r.text, features="lxml")
    text = bs.find("a", {"title": filename}).text
    text = text.replace("#", "")
    return "https://imslp.org/wiki/Special:ReverseLookup/" + text


def get_score():
    """
    https://imslp.org/wiki/Special:ImagefromIndex/359599 ->
    https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/359599/rfpg -> sets cookie and redir to
    http://imslp.org/wiki/Special:IMSLPImageHandler/359599 -> https -> request with cookie and ->
    Location: https://imslp.simssa.ca/files/imglnks/usimg/3/3e/IMSLP359599-PMLP580712-07_affer_opem.zip

    https://imslp.org/wiki/File:PMLP580712-07_affer_opem.zip ->
    https://imslp.org/images/3/3e/PMLP580712-07_affer_opem.zip (disclaimer accept page)


    https://imslp.org/wiki/File:PMLP580712-07_affer_opem.pdf ->
    https://imslp.org/images/6/6b/PMLP580712-07_affer_opem.pdf -> shows disclaimer accept page
    https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/6/6b/PMLP580712-07_affer_opem.pdf/rfpg
    -> sets cookie and redir to ->
    http://imslp.org/wiki/Special:IMSLPImageHandler/6%2F6b%2FPMLP580712-07_affer_opem.pdf%2Frfpg
    -> redir to https -> request with cookie and ->
    https://ks.imslp.info/files/imglnks/usimg/6/6b/IMSLP359598-PMLP580712-07_affer_opem.pdf


    """
    pass


def filter_works_for_xml(work_names):
    """Given a list of work names, bulk load them an only return those which have an xml
    file attached to them (File Description contains "XML") """

    total_works = len(work_names)
    current_works = 0
    all_xml_works = []
    for pages in chunks(work_names, 50):
        current_works += len(pages)
        print("{}/{}".format(current_works, total_works), file=sys.stderr)
        work_pages = get_wiki_content_for_pages(pages)
        xml_work_pages = [w['title'] for w in work_pages if page_has_mxml(w)]
        all_xml_works.extend(xml_work_pages)
    return all_xml_works


def get_composers_for_works(work_names):
    """Given a list of works, get a unique list of composers for each of them.

    Requires an individual lookup for each work name
    """
    total_works = len(work_names)
    composers = set()

    for index, work_name in enumerate(work_names, 1):
        print("{}/{}".format(index, total_works), file=sys.stderr)
        page_contents = imslp_api_raw_query(work_name)
        page = page_contents.get('0')
        if page:
            composers.add(page['parent'])
    return sorted(list(composers))


def page_has_mxml(work):
    """Take a page from `get_wiki_content_for_pages` and see if the mediawiki
    text contains an XML file"""
    parsed = mwph.parse(work["content"])
    templates = parsed.filter_templates()
    if len(templates):
        # The first template is `#fte:imslppage`, and this contains many parameters.
        # We iterate through all paramters and see which ones are themselves a template
        page = templates[0]
        for param in page.params:
            param_templates = param.value.filter_templates()
            for pt in param_templates:
                # Eventually we find the imslpfile template. This template's parameters
                # contains filenames and descriptions
                if pt.name.strip() == "#fte:imslpfile":
                    for fileparam in pt.params:
                        if "File Description" in fileparam.name and "XML" in fileparam.value:
                            return True
    return False


"""
categories = imslp.category_pagelist("For unaccompanied chorus")
xml_works = imslp.filter_works_for_xml(categories)
composers = imslp.get_composers_for_works(xml_works)


"""


"""
Main Category: For unaccompanied chorus


Wikitext for an imslp page
{{#fte:imslppage

| *****AUDIO***** =

===Synthesized/MIDI===
=====For 2 Trumpets and 2 Trombones (Rondeau)=====
{{#fte:imslpaudio
|File Name 1=PMLP98884-ResAcGotSco.mp3
|File Description 1=Virtual performance
|Performers=MIDI
|Performer Categories=
|Uploader=[[User:Michrond|Michrond]]
|Date Submitted=2015/7/8
|Publisher Information=Michel Rondeau
|Copyright=Creative Commons Attribution 4.0
|Misc. Notes={{WIMAProject}}
}}

| *****FILES***** =

{{#fte:imslpfile
|File Name 1=PMLP98884-Resinarius_Ach_Gott_Himmel.pdf
|File Description 1=Complete Score
|Page Count 1=2
|Editor={{LinkEd|Johannes|Wolf}} (1869–1947)<br>{{LinkEd|Hans Joachim|Moser}} (1889–1967)
|Image Type=Normal Scan
|Scanner=University Music Editions
|Uploader=[[User:Homerdundas|homerdundas]]
|Date Submitted=2009/11/18
|Publisher Information=Newe deudsche geistliche Gesenge für die gemeinen Schulen.<br>Gedrückt zu Wittemberg/durch Georgen Rhau, 1544.<br>
{{DeutscherTonkunstReissue|34|1908|XXXIV|1958}}
|Copyright=Public Domain
|Misc. Notes=
}}

===Arrangements and Transcriptions===
=====For 2 Trumpets and 2 Trombones (Rondeau)=====
{{#fte:imslpfile
|File Name 1=PMLP98884-ResAcGotALL.pdf
|File Name 2=PMLP98884-ResAcGot.zip
|File Description 1=Complete Score & Parts
|File Description 2=Engraving files (Finale & XML)
|Arranger={{LinkArr|Michel|Rondeau}}
|Editor=
|Image Type=Typeset
|Scanner=arranger
|Uploader=[[User:Michrond|Michrond]]
|Date Submitted=2015/7/8
|Publisher Information=Michel Rondeau
|Copyright=Creative Commons Attribution 4.0
|Misc. Notes={{WIMAProject}}
}}

| *****WORK INFO*****

|Work Title=Ach Gott von Himmel, sieh darein
|Alternative Title=
|Opus/Catalogue Number=
|Key=
|Number of Movements/Sections=
|Average Duration=
|Dedication=
|First Performance=
|Year/Date of Composition=
|Year of First Publication=1544
|Librettist={{LinkLib|Martin|Luther}} (1483-1546)
|Language=German
|Piece Style=Renaissance
|Instrumentation=SATB voices
|Tags=chorales ; sop alt ten bass ; ch ; de

| *****COMMENTS***** =



| *****END OF TEMPLATE***** }}
"""
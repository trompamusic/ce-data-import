import base64
import json
import re
import unicodedata
import urllib

from bs4 import BeautifulSoup
import requests
from mediawiki import mediawiki
import mwparserfromhell as mwph
from requests.adapters import HTTPAdapter

from ceimport import cache

s = requests.Session()
adapter = HTTPAdapter(max_retries=5)
s.mount("https://", adapter)
s.mount("http://", adapter)


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
    r = s.get(source, headers=headers)
    r.raise_for_status()
    return r.text


def special_link_to_download_url(special_link, download_id):
    url = ""
    r = s.get(url, cookies={"imslpdisclaimeraccepted": "yes"}, allow_redirects=False)
    location = r.headers['Location']
    return location


def mxml_link_to_mediaobject(mxl_link, title):
    m_link_dict = {}

    # mxl_str = read_source(mxl_link['href'])
    # mxl_bs = BeautifulSoup(mxl_str, features="lxml")
    # mxl_final_link = 'https://imslp.org' + mxl_bs.find_all('a', text=re.compile('download'))[0]['href']

    link_parent = mxl_link.parent.parent.parent.parent.parent
    # pubs = link_parent.find_all(text=re.compile('Arranger|Editor'))[0].parent.parent.find('td').find('a')
    # TODO: Publisher or transcriber or arranger should be a relation
    # m_link_dict['Publisher'] = pubs.getText()
    # m_link_dict['Publisher_url'] = 'https://imslp.org' + pubs['href']
    # TODO: Should this be a link to cc.org?
    m_link_dict['license'] = 'https://imslp.org' + \
                             link_parent.find_all(text=re.compile('Copy'))[0].parent.parent.find('td').find_all(
                                 'a')[0]['href']
    # m_link_dict['format'] = 'application/zip'
    m_link_dict['format_'] = 'text/html'
    # TODO: For imslp this is the special download page. We should also add url which is the end url,
    #  and contentUrl, which is the path to the xml inside the zip
    m_link_dict['source'] = mxl_link['href']
    # TODO: Use applcation/zip for contentFormat

    if 'Misc. Notes' in link_parent.getText():
        pub_desc = link_parent.find_all(
            text=re.compile('Misc. Notes')
        )[0].parent.parent.getText().replace('\n', '').replace('Misc. Notes', '')
        pub_desc = unicodedata.normalize('NFKC', pub_desc).strip()
        m_link_dict['description'] = pub_desc

    m_link_dict['title'] = title
    m_link_dict['contributor'] = "https://imslp.org/"

    return m_link_dict


def composition_wikitext_to_music_composition(wikitext):
    parsed = mwph.parse(wikitext["content"])
    url = wikitext["title"].replace(" ", "_")
    composer = None
    inlanguage = None
    name = None

    # TODO: License
    for template in parsed.filter_templates():
        if template.name == "Composer":
            composer = template.params[0]
        if template.name == "Language":
            inlanguage = template.params[0]
        if template.name == "Title":
            # Title has italics markings, so we parse it again an get just the text
            # filter_text() returns [Title, thetitle]
            name = mwph.parse(template).filter_text()[1]

    # We don't get this from the <title>, but just construct it to prevent having
    #  to make another query
    title = f"{wikitext['title']} - ChoralWiki"
    work_dict = {
        # This is the title of the page, so it includes the header
        'title': title,
        'name': name,
        'contributor': 'https://cpdl.org/',
        'source': f'https://cpdl.org/wiki/index.php/{url}',
        'format_': 'text/html',
        'language': 'en',
        'inlanguage': inlanguage
    }

    return {"work": work_dict,
            "composer": composer}


def get_composition_page(source):
    """
    Returns: Work dict, composer url
    """

    title = "Affer opem (Lange, Gregor) - IMSLP: Free Sheet Music PDF Download"
    if source.startswith("//"):
        source = 'https:' + source

    language_mapping = {'english': 'en',
                        'german': 'de',
                        'spanish': 'es',
                        'french': 'fr',
                        'dutch': 'nl',
                        'catalan': 'ca'}
    language_code = None
    if language:
        language_code = language_mapping.get(language.lower())
        if language_code is None:
            print(f"No mapping for lanugage {language}")

    return {'title': title,
            'name': name,
            'source': source,
            'format_': 'text/html',
            'contributor': 'https://imslp.org',
            'language': language_code,
            }, composer


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


def get_wiki_content_for_pages(pages):
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

    r = requests.get(url, params=params)

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
    base_url = "https://imslp.org/imslpscripts/API.ISCR.php?account=worklist/disclaimer=accepted/sort=id/type=2/start={}/retformat=json"
    hasnext = True
    start = 0
    alldata = []
    while hasnext:
        url = base_url.format(start)
        print(url)
        r = requests.get(url)
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


def api_composers_for_works(all_pages_file, works_file):
    """Given a file ``all_pages_file`` from api_all_pages, and a list of works in `works_file`,
    return a unique list of composer categories for all of these works"""
    with open(all_pages_file) as fp:
        j = json.load(fp)

    with open(works_file) as fp:
        works = set(fp.read().splitlines())
    composers = set()
    for work in j:
        if work['id'] in works:
            composers.add(work['parent'])

    return sorted(list(composers))


def parse_imslp_date(year, month, day):
    """Return a date from imslp. Only return if all 3 components exist, and are integers
    This prevents parsing items that only have some components (e.g. yyyy-mm), or approximate
    values (e.g. c 1600)"""
    if year and month and day:
        try:
            int(year)
            int(month)
            int(day)
            return f"{year}-{month}-{day}"
        except ValueError:
            return None


@cache.dict()
def imslp_api_raw_query(page_name):
    page_id = base64.b64encode(urllib.parse.quote(page_name).encode("utf-8"))
    page_id = page_id.decode('utf-8')
    url = f"https://imslp.org/imslpscripts/API.ISCR.php?retformat=json/disclaimer=accepted/type=0/id={page_id}"
    r = s.get(url)
    return r.json()


@cache.dict()
def api_composer_get_relations(composer_name):
    j = imslp_api_raw_query(composer_name)

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


@cache.dict()
def api_composer(composer_name):
    """Arguments:
          composer_name: an imslp Category name for a composer"""
    j = imslp_api_raw_query(composer_name)

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
    bs = BeautifulSoup(page, features="lxml")
    title = bs.find("title")
    if title:
        title = title.text
    else:
        title = None

    return {
        'contributor': 'https://imslp.org/',
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


def api_work(work_name):
    # Ach Gott vom Himmel sieh darein (Resinarius, Balthasar)
    pass


# List of pages
# Get pages in bulk
# for each page, see if there is an xml
# for each xml, import
#   - make api call (this is to get the composer)
#   - return data with a combination of api data and mediawiki data

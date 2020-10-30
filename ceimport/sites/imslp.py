import base64
import json
import re
import unicodedata
import urllib

from bs4 import BeautifulSoup
import requests
from mediawiki import mediawiki
from requests.adapters import HTTPAdapter

from ceimport import cache

s = requests.Session()
adapter = HTTPAdapter(max_retries=5)
s.mount("https://", adapter)
s.mount("http://", adapter)


def get_mediawiki(url):
    return mediawiki.MediaWiki(url=url, rate_limit=True)


def get_titles_in_category(mw, category):
    """Get a list of works constrained by the category from the specified URL

    Arguments:
        mw: a MediaWiki object pointing to an API
        category: the category title to get page titles from
    """
    return mw.categorymembers(category, results=None, subcategories=True)[0]


def get_mw_page_contents(mw, title):
    """Get the contents of a page named `title`.

    Arguments:
        mw: a MediaWiki object pointing to an API
        title: the title of the page to get
    """
    return mw.page(title)


def check_mxl(page_text, keywords):
    """Check if a page has a certain keyword.
    Used for checking if the input page has MXL files
    """

    for keyword in keywords:
        if keyword in page_text:
            return True

    return False


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


def get_composer_from_work_page(bs_file):
    """Find the name and URL of a composer from an HTML page.

    Returns:
        a dictionary containing the name of the composer and the URL
    """
    composer = bs_file.find(class_="wi_body").find_all(text='Composer\n')[0].parent.parent.find('td').contents[0]
    composer_url = 'https://imslp.org' + composer['href']
    return composer_url


def find_name(title_file):
    """Find the title of the work.

    Returns:
        a string with the normalized name of work.
    """
    work_title = title_file.find('th', text=re.compile('Work Title'))
    name = None
    if work_title:
        name_node = work_title.parent.find('td')
        if name_node:
            name = name_node.text.strip()
            name = unicodedata.normalize('NFKC', name)
    return name


def find_lang(title_file):
    """Find the title of the work.

    Returns:
        a string with the normalized name of work.
    """
    # TODO: Convert to iso code
    if 'Language' in title_file.getText():
        language = title_file.find('th', text=re.compile('Language')).parent.find('td').text
        return language.strip()
    else:
        return None


def find_woo(title_file):
    """Find the WoO catalog number of the work.

    Returns:
        a string with the normalized catalog number of the work.
    """
    if 'Opus/Catalogue Number' in title_file.getText():
        woo = title_file.find_all(text=re.compile('Opus/Catalogue Number'))[0].parent.parent.parent.find('td').contents[0].string
        return woo.strip()
    else:
        return None


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


def find_mxl_links(bs_work):
    """Find links to mxml zip downloads on a composition page"""
    mxl_links = [x.parent.parent for x in bs_work.find_all(text=re.compile('XML')) if x.parent.parent.name == 'a']
    mxl_links_out = []

    title = bs_work.find("title")
    if title:
        title = title.text

    for m_link in mxl_links:
        mxl_links_out.append(mxml_link_to_mediaobject(m_link, title))

    return mxl_links_out


def get_composition_page(source):
    """
    Returns: Work dict, composer url, files (list)
    """
    # TODO: Use JSON API:
    """
    https://imslp.org/imslpscripts/API.ISCR.php?account=worklist/disclaimer=accepted/sort=id/type=2/start=0/retformat=json
    Base 64 name in the id param
    https://imslp.org/imslpscripts/API.ISCR.php?retformat=json/disclaimer=accepted/type=0/id=MTIgRWFzeSBQcmVsdWRlcyBmb3IgSGFycCAoQ3JhdmVuLCBKb2huIFRob21hcyk=
    """

    if source.startswith("//"):
        source = 'https:' + source
    page = read_source(source)
    bs = BeautifulSoup(page, features="lxml")
    title = bs.find("title")
    if title:
        title = title.text

    name = find_name(bs)
    composer = get_composer_from_work_page(bs)
    language = find_lang(bs)
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

    mxl_links_out = find_mxl_links(bs)

    return {'title': title,
            'name': name,
            'source': source,
            'format_': 'text/html',
            'contributor': 'https://imslp.org',
            'language': language_code,
            }, composer, mxl_links_out


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
    mw = get_mediawiki('https://imslp.org/api.php')

    list_of_titles = get_pages_for_category(mw, category_name)
    return list_of_titles


def scrape_imslp(list_of_titles: str, select_mxml: bool, page_name: str, num_pages: int):
    print("Got {} compositions".format(len(list_of_titles)))
    mw = get_mediawiki('https://imslp.org/api.php')

    all_works = []
    count_xml = 0

    for count_total, title in enumerate(list_of_titles, 1):
        page = get_mw_page_contents(mw, title)
        has_mxml = check_mxl(page.html, ['MusicXML', 'XML'])

        if not select_mxml or has_mxml:
            work_data, composer, files = get_composition_page(page.url)
            all_works.append(work_data)
            count_xml += 1

    return all_works


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
def api_composer_raw_query(composer_name):
    composer_id = base64.b64encode(urllib.parse.quote(composer_name).encode("utf-8"))
    composer_id = composer_id.decode('utf-8')
    url = f"https://imslp.org/imslpscripts/API.ISCR.php?retformat=json/disclaimer=accepted/type=0/id={composer_id}"
    r = s.get(url)
    return r.json()


@cache.dict()
def api_composer_get_relations(composer_name):
    j = api_composer_raw_query(composer_name)

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
    j = api_composer_raw_query(composer_name)

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


def main(category_names, output_name, select_mxml=True, page_name=None, num_pages=None):

    works = set()
    composers = set()
    all_pages = None
    for category in category_names:
        pages = category_pagelist(category)
        print(f"got {len(pages)} pages")

        if all_pages is None:
            all_pages = set(pages)
        else:
            all_pages = all_pages & set(pages)
    print(f"intersection is {len(all_pages)} items")

    works = scrape_imslp(all_pages, select_mxml, page_name, num_pages)
    composers = scrape_composers(works)

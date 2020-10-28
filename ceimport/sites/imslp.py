import re
import unicodedata

from bs4 import BeautifulSoup
import requests
from mediawiki import mediawiki
from requests.adapters import HTTPAdapter

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
    r = s.get(source)
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


def process_composer(composer_source):
    """Extract information about a composer from an HTML page.

    Returns:
        a dictionary with the name, url, biography, wikipedia link, date of birth and date of death of the composer.
    """
    # TODO: external links, use to cross-link to musicbrainz, wikipedia, viaf, worldcat, loc

    page = read_source(composer_source)
    bs = BeautifulSoup(page, features="lxml")

    title = bs.find("title")
    if title:
        title = title.text

    composer = bs.find("span", {"class": "mw-headline"})
    if composer:
        composer = composer.text
        composer = unicodedata.normalize('NFKC', composer).strip()

    # dates
    dates = bs.find("div", {"class": "cp_firsth"})
    if dates:
        match = re.search(r"\(.*?\)", dates.text)
        if match:
            dates = match.group()
            date_parts = dates.split("—")
            if len(date_parts) == 2:
                date_from = date_parts[0]
                date_to = date_parts[1]
                # TODO: Parse dates and add if they are valid

    return {
        'title': title,
        'name': composer,
        'contributor': 'https://imslp.org/',
        'source': composer_source,
        'format_': 'text/html',
        'language': 'en'
    }


def find_name(title_file):
    """Find the title of the work.

    Returns:
        a string with the normalized name of work.
    """
    name = title_file.find_all(text=re.compile('Work Title'))[0].parent.parent.find('td').contents[0].string
    name = unicodedata.normalize('NFKC', name).strip()
    return name


def find_lang(title_file):
    """Find the title of the work.

    Returns:
        a string with the normalized name of work.
    """
    # TODO: Convert to iso code
    if 'Language' in title_file.getText():
        language = title_file.find_all(text=re.compile('Language'))[0].parent.parent.find('td').contents[0].string
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
    m_link_dict['format'] = 'text/html'
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
    woo = find_woo(bs)

    mxl_links_out = find_mxl_links(bs)

    return {'title': title,
            'name': name,
            'source': source,
            'language': language,
            'catalog': woo
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


def scrape_composers(works):
    seen_composers = set()
    all_composers = []

    composers = [w['Creator'] for w in works]
    for c in composers:
        if c not in seen_composers:
            dict_comp = process_composer(c)
            all_composers.append(dict_comp)
            seen_composers.add(c)

    return all_composers


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

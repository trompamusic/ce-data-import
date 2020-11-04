import re

import mediawiki
import requests
import mwparserfromhell as mwph

from ceimport import chunks


def get_mediawiki():
    return mediawiki.MediaWiki(url='http://www.cpdl.org/wiki/api.php', rate_limit=True)


def get_wiki_content_for_pages(pages):
    if len(pages) > 50:
        raise ValueError("can only do up to 50 pages")

    query = "|".join(pages)
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": query,
        "rvslots": "main",
        "rvprop": "content",
        "formatversion": "2",
        "format": "json"
    }
    url = 'http://www.cpdl.org/wiki/api.php'

    r = requests.get(url, params=params)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        return []

    pages = j.get("query", {}).get("pages", [])

    """
    cpdl api returns a list of pages
      -> this is different to the imslp one
    """
    ret = []
    for page in pages:
        if "invalid" in page:
            # TODO Logging, reason in "invalidreason"
            pass

        title = page["title"]
        revisions = page.get("revisions")
        if revisions:
            text = revisions[0].get("slots", {}).get("main", {}).get("content")
            ret.append({"title": title, "content": text})

    return ret


def get_works_with_xml(pages):
    """
    Arguments:
        pages: result of `get_wiki_content_for_pages`
    """
    ret = []
    for page in pages:
        if "{{XML}}" in page["content"]:
            ret.append(page)
    return ret


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


def composition_wikitext_to_mediaobjects(wikitext):
    pass


def composer_wikitext_to_person(wikitext):
    parsed = mwph.parse(wikitext["content"])
    name = wikitext["title"]
    url = name.replace(" ", "_")
    # TODO: Born, Died, Biography, Image

    # TODO: WikipediaLink, IMSLP, IMSLP2 tags
    for template in parsed.filter_templates():
        if template.name == "WikipediaLink":
            pass
        if template.name == "IMSLP" or template.name == "IMSLP2":
            pass

    # We don't get this from the <title>, but just construct it to prevent having
    #  to make another query
    title = f"{name} - ChoralWiki"

    return {
        'title': title,
        'name': name,
        'contributor': 'https://cpdl.org/',
        'source': f'https://cpdl.org/wiki/index.php/{url}',
        'format_': 'text/html',
        'language': 'en',
    }


def get_composers_for_works(works):
    # TODO: This is inefficient because we query all works and then throw away the data
    composers = set()
    num_iterations = int(len(works) / 50)
    i = 1
    for items in chunks(works, 50):
        print(f"{i}/{num_iterations}")
        i += 1
        pages = get_wiki_content_for_pages(items)
        xmlpages = get_works_with_xml(pages)
        for page in xmlpages:
            composition = composition_wikitext_to_music_composition(page)
            composer = composition['composer']
            composers.add(str(composer))

    return sorted(list(composers))


def get_titles_in_category(category):
    """Get a list of works constrained by the category from the specified URL

    Arguments:
        md: a MediaWiki object pointing to an API
        category: the category title to get page titles from
    """
    mw = get_mediawiki()
    return mw.categorymembers(category, results=None, subcategories=True)[0]


def find_mxl(bs_file):
    mxl = bs_file.find_all('a', href=re.compile('xml'))[0]
    formatmaxl = 'application/vnd.recordare.musicxml+xml'

    mxl = bs_file.find_all('a', href=re.compile('MXL'))[0]
    formatmaxl = 'application/vnd.recordare.musicxml'


def main():
    list_of_titles = get_titles_in_category("4-part choral music")

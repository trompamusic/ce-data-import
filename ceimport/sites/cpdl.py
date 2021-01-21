import os
import re
from typing import List

import mediawiki
import requests
import mwparserfromhell as mwph

from ceimport import chunks, cache


def get_mediawiki():
    return mediawiki.MediaWiki(url='http://www.cpdl.org/wiki/api.php', rate_limit=True)


@cache.dict()
def get_fileurl_from_media(media: List[str]):
    if len(media) > 50:
        raise ValueError("can only do up to 50 pages")

    query = "|".join(media)
    params = {"action": "query",
              "prop": "imageinfo",
              "titles": query,
              "format": "json",
              "iiprop": "url"}
    url = 'http://www.cpdl.org/wiki/api.php'

    r = requests.get(url, params=params)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        return []

    normalised = j.get('query', {}).get('normalized', [])
    norm_mapping = {}
    for n in normalised:
        norm_mapping[n['from']] = n['to']

    pages = j.get("query", {}).get("pages", [])

    image_info = {}
    for k, v in pages.items():
        info = v.get('imageinfo')
        if info:
            image_info[v['title']] = info[0]

    ret = []
    for m in media:
        m = norm_mapping.get(m, m)
        if m in image_info:
            ret.append(image_info[m])

    return ret


@cache.dict()
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

    # TODO: License (musiccomposition or mediaobject?)
    # TODO: IMSLP work page?
    # TODO: Sometimes there is more than one composer
    for template in parsed.filter_templates():
        if template.name == "Composer":
            composer = str(template.params[0])
        if template.name == "Language":
            inlanguage = str(template.params[0])
        if template.name == "Title":
            # Title has italics markings, so we parse it again an get just the text
            # filter_text() returns [Title, thetitle]
            name = str(mwph.parse(template).filter_text()[1])

    # We don't get this from the <title>, but just construct it to prevent having
    #  to make another query
    title = f"{wikitext['title']} - ChoralWiki"
    work_dict = {
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


def get_xml_files_from_composition_wikitext(wikitext):
    parsed = mwph.parse(wikitext['content'])
    wikilinks = parsed.filter_wikilinks()
    wikilinks = [w for w in wikilinks if w.text == "{{XML}}"]

    return [str(w.title) for w in wikilinks]


def composition_wikitext_to_mediaobjects(wikitext):
    xml_files = get_xml_files_from_composition_wikitext(wikitext)
    xml_files = [x.replace("Media:", "File:") for x in xml_files]

    file_urls = get_fileurl_from_media(xml_files)
    ret = []

    for f in file_urls:
        url = f['url']
        descriptionurl = f['descriptionurl']
        if url.endswith(".xml"):
            format = 'application/vnd.recordare.musicxml+xml'
        elif url.endswith(".mxl"):
            format = 'application/vnd.recordare.musicxml'
        else:
            continue
        # TODO: Should this filename have the 'File:' prefix?
        filename = os.path.basename(descriptionurl)
        title = f"{filename} - ChoralWiki"

        mediaobject = {
            'title': title,  # <title> of html
            'name': filename,  # name of file
            'contributor': 'https://cpdl.org/',
            'source': descriptionurl,  # url of a webpage about the file
            'contenturl': url,  # url to the actual file
            'encodingformat': format,  # mimetype of the actual file
            'format_': 'text/html'  # mimetype of the webpage (source)
        }
        ret.append(mediaobject)
    return ret


def composer_wikitext_to_person(wikitext):
    parsed = mwph.parse(wikitext["content"])
    name = wikitext["title"]
    url = name.replace(" ", "_")
    # TODO: Born, Died, Biography, Image

    wikipedia = None
    imslp = None
    # If the IMSLP and WikipediaLink tags have no parameter, it means that the page on the other
    # site is the same as on CPDL. If there is a param it's the
    for template in parsed.filter_templates():
        if template.name == "WikipediaLink" or template.name == "WikipediaLink2":
            if template.params:
                wikipedia = str(template.params[0])
            else:
                wikipedia = name
            wikipedia = "https://en.wikipedia.org/wiki/" + wikipedia
        if template.name == "IMSLP":
            # IMSLP pages follow the format "Surname, Name". We assume that the last word after
            # whitespace is the surname
            if template.params:
                imslp = str(template.params[0])
            else:
                imslp = name
            parts = imslp.split(" ")
            if len(parts) > 1:
                imslp = parts[-1] + ", " + " ".join(parts[:-1])
            imslp = "https://imslp.org/wiki/Category:" + imslp

    # We don't get this from the <title>, but just construct it to prevent having
    #  to make another query
    title = f"{name} - ChoralWiki"

    cpdl = {
        'title': title,
        'name': name,
        'contributor': 'https://cpdl.org/',
        'source': f'https://cpdl.org/wiki/index.php/{url}',
        'format_': 'text/html',
        'language': 'en',
    }

    return {
        "cpdl": cpdl,
        "wikipedia": wikipedia,
        "imslp": imslp
    }


def get_wikitext_for_titles(titles):
    num_iterations = int(len(titles) / 50)
    i = 1
    all_pages = []
    for items in chunks(titles, 50):
        print(f"{i}/{num_iterations}")
        i += 1
        pages = get_wiki_content_for_pages(items)
        all_pages.extend(pages)

    return all_pages


def get_composers_for_works(works):
    """
    :param works: the result of get_wikitext_for_titles or get_works_with_xml (filtered version)
    :return: a unique list of composer names
    """
    composers = set()
    for work in works:
        composition = composition_wikitext_to_music_composition(work)
        composers.add(str(composition['composer']))

    return sorted(list(composers))


def get_titles_in_category(category):
    """Get a list of works constrained by the category from the specified URL

    Arguments:
        md: a MediaWiki object pointing to an API
        category: the category title to get page titles from
    """
    mw = get_mediawiki()
    return mw.categorymembers(category, results=None, subcategories=True)[0]


def main():
    titles = cpdl.get_titles_in_category("4-part choral music")
    wikitext = cpdl.get_wikitext_for_titles(titles)
    xmlwikitext = cpdl.get_works_with_xml(wikitext)
    composers = get_composers_for_works(xmlwikitext)
    composerwiki = cpdl.get_wikitext_for_titles(composers)


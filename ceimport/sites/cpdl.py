import os
from typing import List

import mediawiki
import requests
import requests_cache
import mwparserfromhell as mwph
from requests.adapters import HTTPAdapter

from ceimport import chunks


session = requests_cache.CachedSession()
adapter = HTTPAdapter(max_retries=5)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_mediawiki():
    return mediawiki.MediaWiki(url='http://www.cpdl.org/wiki/api.php', rate_limit=True)


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

    r = session.get(url, params=params)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        return []

    normalised = j.get('query', {}).get('normalized', [])
    norm_mapping = {}
    for n in normalised:
        norm_mapping[n['from']] = n['to']

    pages = j.get("query", {}).get("pages", {})

    image_info = {}
    for k, v in pages.items():
        info = v.get('imageinfo')
        if info:
            image_info[v['title']] = info[0]

    ret = {}
    for m in media:
        norm = norm_mapping.get(m, m)
        if norm in image_info:
            ret[m] = image_info[norm]

    return ret


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

    try:
        r = session.get(url, params=params)
    except requests.exceptions.ConnectionError:
        return []
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
        'contributor': 'https://cpdl.org',
        'source': f'https://cpdl.org/wiki/index.php/{url}',
        'format_': 'text/html',
        'language': 'en',
        'inlanguage': inlanguage
    }

    return {"work": work_dict,
            "composer": composer}


def get_file_pairs_from_composition_wikitext(wikitext):
    """
    CPDL Wikitext has lines like this:
    *{{PostedDate|2014-11-24}} {{CPDLno|33477}} [[Media:Torrejon-A_este_sol_peregrino.pdf|{{pdf}}]] [[Media:Torrejon-A_este_sol_peregrino.mid|{{mid}}]] [[Media:Torrejon-A_este_sol_peregrino.mxl|{{XML}}]] [[Media:Torrejon-A_este_sol_peregrino.musx|{{F14}}]] (Finale 2014)
    Look for these, and return ones that include an {{XML}} link. If there is also a PDF, return that too
    """
    parsed = mwph.parse(wikitext['content'])

    # Look for nodes which are {{CPDLno}} templates
    cpdl_nodes = [template for template in parsed.filter_templates() if template.name == 'CPDLno']
    cpdl_nodes.append(parsed.nodes[-1])

    ret = []

    # For each of these nodes, from the node to the next, see if there is
    # a wikilink with {{XML}}. If so, return both the pdf in this range if it exists
    # and the xml file
    # e.g. nodes 3, 12, 15. We append the last node so that we can group them
    # into 3-12, 12-15, 15-end
    parsed_nodes = parsed.nodes
    for i in range(len(cpdl_nodes)-1):
        start = cpdl_nodes[i]
        end = cpdl_nodes[i+1]
        try:
            start_i = parsed_nodes.index(start)
            end_i = parsed_nodes.index(end)
        except ValueError:
            continue
        relevant_nodes = parsed_nodes[start_i:end_i]
        wikilinks = [n for n in relevant_nodes if isinstance(n, mwph.nodes.Wikilink)]
        xml_templates = [str(n.title) for n in wikilinks if n.text == "{{XML}}"]
        pdf_templates = [str(n.title) for n in wikilinks if n.text == "{{pdf}}"]

        if len(xml_templates) == 1 and len(pdf_templates) in [0, 1]:
            xml = xml_templates[0]
            pdf = pdf_templates[0] if len(pdf_templates) else None
            data = {"xml": xml.replace("Media:", "File:")}
            if pdf:
                data["pdf"] = pdf.replace("Media:", "File:")

            ret.append(data)

    return ret


def composition_wikitext_to_mediaobjects(wikitext):
    files = get_file_pairs_from_composition_wikitext(wikitext)
    file_names = []
    for f in files:
        file_names.append(f["xml"])
        if "pdf" in f and f["pdf"]:
            file_names.append(f["pdf"])

    file_urls = get_fileurl_from_media(file_names)
    ret = []

    for f in files:
        xml = f["xml"]
        xml_url = file_urls.get(xml)
        if not xml_url:
            continue
        url = xml_url['url']
        descriptionurl = xml_url['descriptionurl']
        if url.endswith(".xml"):
            format = 'application/vnd.recordare.musicxml+xml'
        elif url.endswith(".mxl"):
            format = 'application/vnd.recordare.musicxml'
        else:
            continue
        # TODO: Should this filename have the 'File:' prefix?
        filename = os.path.basename(descriptionurl)
        title = f"{filename} - ChoralWiki"

        xmlmediaobject = {
            'title': title,  # <title> of html
            'name': filename,  # name of file
            'contributor': 'https://cpdl.org',
            'source': descriptionurl,  # url of a webpage about the file
            'contenturl': url,  # url to the actual file
            'encodingformat': format,  # mimetype of the actual file
            'format_': 'text/html'  # mimetype of the webpage (source)
        }

        pdfmediaobject = None
        if "pdf" in f:
            pdf = f["pdf"]
            pdf_url = file_urls.get(pdf)
            if pdf_url:
                url = pdf_url['url']
                descriptionurl = pdf_url['descriptionurl']
                format = 'application/pdf'
                # TODO: Should this filename have the 'File:' prefix?
                filename = os.path.basename(descriptionurl)
                title = f"{filename} - ChoralWiki"

                pdfmediaobject = {
                    'title': title,  # <title> of html
                    'name': filename,  # name of file
                    'contributor': 'https://cpdl.org',
                    'source': descriptionurl,  # url of a webpage about the file
                    'contenturl': url,  # url to the actual file
                    'encodingformat': format,  # mimetype of the actual file
                    'format_': 'text/html'  # mimetype of the webpage (source)
                }

        ret.append({"xml": xmlmediaobject, "pdf": pdfmediaobject})
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
        'contributor': 'https://cpdl.org',
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


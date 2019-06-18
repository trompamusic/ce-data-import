# Get descriptions from Wikipedia based on a wikidata link

from wikidata.client import Client
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

s = requests.Session()
adapter = HTTPAdapter(max_retries=5, pool_connections=100, pool_maxsize=100)
s.mount("https://", adapter)


class WikipediaException(Exception):
    pass


def _get_normalized_query(data, query):
    """If you query with an _ in a query (e.g. from a wikipedia url, then wikipedia will "normalize" it,
    so that it doesn't have the _ or other characters in it"""
    normalized = data.get("query", {}).get("normalized")
    if normalized:
        for n in normalized:
            if n["from"] == query:
                return n["to"]

    return query


def parse_description_from_wikipedia_response(title, data):
    pages = data.get("query", {}).get("pages")
    title = _get_normalized_query(data, title)
    for pid, pdata in pages.items():
        if pdata["title"] == title:
            return pdata["extract"]
    return ""


def get_wikidata_id_from_wikipedia_url(wp_url):
    """Get the wikidata id for this URL if it exists
    Returns None if the page has no wikidata id"""
    
    if "en.wikipedia.org" not in wp_url:
        raise WikipediaException("Can only use en.wikipedia.org urls")
    parts = urlparse(wikidata_url)
    # Remove /wiki/  (some titles may have / in them so we can't take the last part)
    wp_title = "/".join(parts[2:])
    param_url = "https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={}&format=json"
    full_url = param_url.format(wp_title)
    r = s.get(full_url)
    data = r.json()
    title = _get_normalized_query(data, wp_title)
    pages = data.get("query", {}).get("pages")
    for pid, pdata in pages.items():
        if pdata["title"] == title:
            return pdata.get("pageprops", {}).get("wikibase_item")
    return None


def get_description_from_wikipedia_url(wp_url):
    if "en.wikipedia.org" not in wp_url:
        raise WikipediaException("Can only use en.wikipedia.org urls")
    parts = urlparse(wikidata_url)
    # Remove /wiki/  (some titles may have / in them so we can't take the last part)
    wp_title = "/".join(parts[2:])
    return get_description_from_wikipedia(wp_title)


def get_description_from_wikipedia(title):
    desc_url = "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&format=json&redirects=1&titles={}"
    full_url = desc_url.format(title)

    r = s.get(full_url)
    data = r.json()
    return parse_description_from_wikipedia_response(title, data)


def get_description_for_wikidata(wikidata_url):
    parts = urlparse(wikidata_url)
    wd_id = parts.path.split("/")[-1]
    c = Client()
    entity = c.get(wd_id, load=True)

    sitelinks = entity.attributes.get("sitelinks", {})
    enwiki = sitelinks.get("enwiki", {})
    title = enwiki.get("title")

    return get_description_from_wikipedia(title)

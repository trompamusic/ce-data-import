# Get descriptions from Wikipedia based on a wikidata link

from wikidata.client import Client
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

s = requests.Session()
adapter = HTTPAdapter(max_retries=5, pool_connections=100, pool_maxsize=100)
s.mount("https://", adapter)


def description_from_wikipedia(title, data):
    pages = data.get("query", {}).get("pages")
    for pid, pdata in pages.items():
        if pdata["title"] == title:
            return pdata["extract"]
    return ""


def get_description_for_wikidata(wikidata_url):
    parts = urlparse(wikidata_url)
    wd_id = parts.path.split("/")[-1]
    c = Client()
    entity = c.get(wd_id, load=True)

    sitelinks = entity.attributes.get("sitelinks", {})
    enwiki = sitelinks.get("enwiki", {})
    title = enwiki.get("title")

    desc_url = "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&format=json&redirects=1&titles={}"
    full_url = desc_url.format(title)

    r = s.get(full_url)
    data = r.json()
    return description_from_wikipedia(title, data)

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from ceimport import cache

s = requests.Session()
adapter = HTTPAdapter(max_retries=5, pool_connections=100, pool_maxsize=100)
s.mount("https://", adapter)
s.mount("http://", adapter)


@cache.dict()
def load_person_from_loc(loc_url):
    """TODO: You can also use this url to load data in rdf/jsonld, which could be used to find links
         to other sources, such as worldcat + isni"""
    try:
        r = s.get(loc_url)
        r.raise_for_status()
        bs = BeautifulSoup(r.content, features="lxml")
        title = bs.find("title")
        if title:
            title = title.text
            return {
                "title": title,
                "contributor": "https://id.loc.gov/",
                "source": loc_url,
                "format_": "text/html"
            }
        return {}
    except requests.exceptions.HTTPError:
        return {}

import json
import sys
import urllib.request

import mediawiki
import requests
from requests.adapters import HTTPAdapter

s = requests.Session()
adapter = HTTPAdapter(max_retries=5)
s.mount("https://", adapter)
s.mount("http://", adapter)


def progress(count, total, suffix=''):
    """
    Helper function to print a progress bar.
    """

    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()


def write_json(list_of_works, file_name):
    """write a dictionary of a list of works to a JSON file.
    """
    with open(file_name, 'w') as fp:
        json.dump(list_of_works, fp, indent=4, sort_keys=True)


def get_mediawiki(url):
    return mediawiki.MediaWiki(url=url, rate_limit=True)


def get_titles_in_category(mw, category):
    """Get a list of works constrained by the category from the specified URL

    Arguments:
        md: a MediaWiki object pointing to an API
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

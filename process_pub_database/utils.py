import json
import sys
import urllib.request

import mediawiki


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
    with open(file_name, 'w') as json_file:
        json.dump(list_of_works, json_file, indent=4, sort_keys=True)


def get_list_of_titles(url, category):
    """Get a list of works constrained by the category from the specified URL
    """
    md = mediawiki.MediaWiki(url=url, rate_limit=True)
    list_of_titles = md.categorymembers(category, results=None, subcategories=True)[0]
    return list_of_titles, md


def check_mxl(md, title, keywords):
    """Check if a page has a certain keyword.
    Used for checking if the input page has MXL files
    """
    ret_page = md.page(title)
    page_text = ret_page.html

    for keyword in keywords:
        if keyword in page_text:
            return ret_page.url

    return None


def read_source(source):
    """
    Function to read a URL and return the HTML string.
    """
    with urllib.request.urlopen(source) as fp:
        mybytes = fp.read()

        mystr = mybytes.decode("utf8")

    return mystr

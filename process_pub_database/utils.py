import mediawiki
import json
import sys
import os,re
import urllib.request

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
	json_file = open(file_name, 'w') 
	json.dump(list_of_works, json_file, indent=4, separators=(',', ': '), sort_keys=True)
	json_file.close()

def get_list_of_titles(url, category):
    md = mediawiki.MediaWiki(url=url, rate_limit=True)
    list_of_titles = md.categorymembers(category,results=None,subcategories=True)[0]
    return list_of_titles, md


def check_mxl(md, title, keywords):
    ret_page = md.page(title)
    page_text = ret_page.html

    for keyword in keywords:

        if keyword in page_text:
            source = ret_page.url
            return True, source
            
    return False, None

def read_source(source):
    fp = urllib.request.urlopen(source)
    mybytes = fp.read()

    mystr = mybytes.decode("utf8")
    fp.close()
    return mystr

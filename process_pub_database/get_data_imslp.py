import argparse
import re
import unicodedata

from bs4 import BeautifulSoup
import utils


def find_composer(bs_file):
    """Find the name and URL of a composer from an HTML page.

    Returns:
        a dictionary containing the name of the composer and the URL
    """
    composer = bs_file.find_all(text='Composer\n')[0].parent.parent.find('td').contents[0]
    composer_name = composer.getText()
    composer_url = 'https://imslp.org' + composer['href']
    composer_name = composer_name.split(',')[1][1:] + ' ' + composer_name.split(',')[0]
    composer_name = unicodedata.normalize('NFKC', composer_name).strip()
    composer = {'Name': composer_name, 'url': composer_url}

    return composer


def process_composer(composer):
    """Extract information about a composer from an HTML page.

    Returns:
        a dictionary with the name, url, biography, wikipedia link, date of birth and date of death of the composer.
    """

    dict_comp = {}

    comp_str = utils.read_source(composer['url'])

    composer_file = BeautifulSoup(comp_str, features="lxml")

    if 'Wikipedia' in composer_file.getText():
        wiki_link = composer_file.find_all('a', text='Wikipedia')[0]['href']
        dict_comp['Wikipedia'] = wiki_link

    dict_comp['Source'] = composer['url']
    dict_comp['Title'] = composer['Name']

    return dict_comp


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
    if 'Language' in title_file.getText():
        language = title_file.find_all(text=re.compile('Language'))[0].parent.parent.find('td').contents[0].string

    else:
        language = 'Unknown'

    return language


def find_mxl_links(title_file, name):
    mxl_links = [x.parent.parent for x in title_file.find_all(text=re.compile('XML')) if x.parent.parent.name == 'a']
    mxl_links_out = []

    for m_link in mxl_links:
        m_link_dict = {}

        mxl_link = m_link['href']

        mxl_str = utils.read_source(mxl_link)

        mxl_bs = BeautifulSoup(mxl_str, features="lxml")
        mxl_final_link = 'https://imslp.org' + mxl_bs.find_all('a', text=re.compile('download'))[0]['href']

        link_parent = mxl_links[0].parent.parent.parent.parent.parent

        pubs = link_parent.find_all(text=re.compile('Arranger|Editor'))[0].parent.parent.find('td').find('a')

        m_link_dict['Publisher'] = pubs.getText()

        m_link_dict['Publisher_url'] = 'https://imslp.org' + pubs['href']

        m_link_dict['File_url'] = mxl_final_link

        m_link_dict['License'] = 'https://imslp.org' + \
                                 link_parent.find_all(text=re.compile('Copy'))[0].parent.parent.find('td').find_all(
                                     'a')[0]['href']

        m_link_dict['Format'] = 'application/zip'

        global_desc = "MusicXML score for {} ".format(name.strip())

        if 'Misc. Notes' in link_parent.getText():
            pub_desc = link_parent.find_all(text=re.compile('Misc. Notes'))[0].parent.parent.getText().replace('\n',
                                                                                                               '').replace(
                'Misc. Notes', '')

            pub_desc = unicodedata.normalize('NFKC', pub_desc).strip()

            m_link_dict['Description'] = global_desc + pub_desc

        mxl_links_out.append(m_link_dict)

        return mxl_links_out


def get_single_page(source):
    print(source)

    title_str = utils.read_source('https:' + source)

    title_file = BeautifulSoup(title_str, features="lxml")

    composer = find_composer(title_file)
    name = find_name(title_file)
    language = find_lang(title_file)

    mxl_links_out = find_mxl_links(title_file, name)

    dict_file = {'Title': name.strip(),
                 'Creator': composer,
                 'Description': "Composition {} by {}".format(name.strip(), composer['Name'].strip()),
                 'Source': source,
                 'Contributor': 'https://www.upf.edu',
                 'Relation': mxl_links_out,
                 'Language': 'en',
                 'Subject': language.replace('\n', '') + ' choir piece'}

    print(dict_file)
    return dict_file


def get_pages_for_category(mw, category_name, page_name=None, num_pages=None):
    print("Getting pages for category {}".format(category_name))
    list_of_titles = utils.get_titles_in_category(mw, category_name)
    if page_name and page_name in list_of_titles:
        return [page_name]
    elif page_name and page_name not in list_of_titles:
        raise Exception("Asked for page '{}' but it's not here".format(page_name))

    if num_pages:
        print("Limiting number of pages to {}".format(num_pages))
        list_of_titles = list_of_titles[:num_pages]

    return list_of_titles


def scrape_imslp(category_name: str, select_mxml: bool, page_name: str, num_pages: int):
    mw = utils.get_mediawiki('https://imslp.org/api.php')

    list_of_titles = get_pages_for_category(mw, category_name, page_name, num_pages)

    count_xml = 0
    all_works = []

    print("Got {} compositions".format(len(list_of_titles)))

    for count_total, title in enumerate(list_of_titles, 1):
        #print(title)
        page = utils.get_mw_page_contents(mw, title)
        has_mxml = utils.check_mxl(page.html, ['MusicXML', 'XML'])

        if has_mxml and select_mxml:
            source = page.url
            work_data = get_single_page(source)

            all_works.append(work_data)
            count_xml += 1

        utils.progress(count_total, len(list_of_titles), " {} files done".format(count_xml))

    return all_works


def scrape_composers(works):
    seen_composers = set()
    all_composers = []

    composers = [w['Creator'] for w in works]
    for c in composers:
        if c['Name'] not in seen_composers:
            dict_comp = process_composer(c)
            all_composers.append(dict_comp)
            seen_composers.add(c['Name'])

    return all_composers


def main(category_name, output_name, select_mxml=True, page_name=None, num_pages=None):

    works = scrape_imslp(category_name, select_mxml, page_name, num_pages)
    composers = scrape_composers(works)

    work_name = "{}.json".format(output_name)
    composer_name = "{}_composers.json".format(output_name)

    utils.write_json(works, work_name)
    utils.write_json(composers, composer_name)


if __name__ == '__main__':
    # default category "For unaccompanied chorus"
    parser = argparse.ArgumentParser(description="Read data from IMSLP")
    parser.add_argument("category", type=str, help="The category to scrape")
    parser.add_argument("-o", help="output filename (without extension)", required=True)
    parser.add_argument("-n", type=int, help="Limit scraping to this many items")
    parser.add_argument("--page", type=str, help="Only scrape this page")
    parser.add_argument("--xml", action="store_true", help="Only scrape pages that have MusicXML")

    args = parser.parse_args()
    main(args.category, args.o, args.xml, args.page, args.n)

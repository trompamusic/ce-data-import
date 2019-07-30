import re
import unicodedata

from bs4 import BeautifulSoup as bs
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

    composer_file = bs(comp_str, features="lxml")

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

        mxl_bs = bs(mxl_str, features="lxml")
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


def main():
    list_of_titles, md = utils.get_list_of_titles('https://imslp.org/api.php', "For unaccompanied chorus")

    print('Info retrieved')

    count_xml = 0
    count_target = 0
    count_total = 0
    count_except = 0
    dict_text = {}
    fails = []
    dict_all = {}

    composers = []

    composer_dict = {}

    for title in list_of_titles:
        count_total += 1

        try:
            # title = 'Et respondens Iesus dixit illis (Lange, Gregor)'

            source = utils.check_mxl(md, title, ['MusicXML', 'XML'])

            if source:
                dict_file = {}

                title_str = utils.read_source('https:' + source)

                title_file = bs(title_str, features="lxml")

                composer = find_composer(title_file)

                if composer not in composers:
                    composers.append(composer)

                    dict_comp = process_composer(composer)

                    composer_dict[composer['Name']] = dict_comp

                name = find_name(title_file)

                language = find_lang(title_file)

                mxl_links_out = find_mxl_links(title_file, name)

                dict_file['Title'] = name.strip()
                dict_file['Creator'] = composer
                dict_file['Description'] = "Composition {} by {}".format(name.strip(), composer['Name'].strip())
                dict_file['Source'] = source
                dict_file['Contributor'] = 'https://www.upf.edu'
                dict_file['Relation'] = mxl_links_out
                dict_file['Language'] = 'en'

                dict_file['Subject'] = language.replace('\n', '') + ' choir piece'

                dict_all[title] = dict_file
                count_xml += 1

        except Exception as e:
            print(title.encode('utf-8'))
            print(e)
            count_except += 1
            print('Fail {}'.format(count_except))

            fails.append(title)

        utils.progress(count_total, len(list_of_titles), " {} files done".format(count_xml))
    utils.write_json(dict_all, 'imslp.json')
    utils.write_json(composer_dict, 'imslp_composers.json')


if __name__ == '__main__':
    main()

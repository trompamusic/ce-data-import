import re
import unicodedata

from bs4 import BeautifulSoup as bs
import utils


def find_composer(bs_file):
    """find the name and URL of a composer from an HTML page.
    Returns:
        a dictionary containing the name of the composer and the URL
    """
    compy = bs_file.find_all('b', text=re.compile('Composer|Editors'))[0].find_next_siblings('a')[0]
    compy_name = compy['title']
    compy_name = unicodedata.normalize('NFKC', compy_name).strip()
    composer = {'Name': compy_name,
                'url': 'https://www.cpdl.org' + compy['href']}
    return composer


def process_composer(comp_str):
    """Extract information about a composer from an HTML page.

    Returns:
         a dictionary with the name, url, biography, wikipedia link, date of birth and date of death of the composer.
    """

    composer_file = bs(comp_str, features="lxml")

    if 'Biography' in comp_str:
        biop = composer_file.find_all('b', text=re.compile('Biography'))[0].parent
        bio = biop.getText().rstrip() + biop.find_next_siblings()[0].getText().strip()
        bio = bio.replace('Biography', '').replace(':', '').strip()
    elif 'Wikipedia article' in comp_str:
        bio = composer_file.find_all(text=re.compile('Wikipedia article'))[0].parent.find_previous_siblings('p')[
            0].getText().strip()
    if 'Wikipedia article' in comp_str:

        wiki_link = composer_file.find_all(text=re.compile('Wikipedia article'))[0].parent.find('a')['href']
    else:
        wiki_link = ''

    if 'Born' in comp_str:
        born = composer_file.find_all(text=re.compile('Born'))[0].parent.next_sibling.string.strip()
    else:
        born = 'Unknown'
    if 'Died' in comp_str:
        died = composer_file.find_all(text=re.compile('Died'))[0].parent.next_sibling.string.strip()
    else:
        died = 'Unknown'

    return {'Biography': bio, 'Wikipedia': wiki_link, 'Born': born, 'Died': died}


def find_name(title_file):
    """Find the title of the work.

    Returns:
        a string with the normalized name of work.
    """
    name = title_file.find_all(text=re.compile('Title:'))[0].parent.contents
    if len(name) > 1:
        name = name[-1]
    else:
        name = title_file.find_all('b', text=re.compile('Title:'))[0].parent.contents
        if len(name) > 1:
            if name[1].isspace():
                name = name[2].string
            else:
                name = name[1].string
        else:
            name = title_file.find_all('b', text=re.compile('Title:'))[0].find_next_siblings()[0].string

    name = unicodedata.normalize('NFKC', name).strip()

    return name


def find_mxl(bs_file):
    """find the MXL file from an HTML page.

    Returns: a dictionary with the link to the MXL file,
            the name of the publisher, with URL of the publisher,
            the associated license and the format.
    """
    page_text = bs_file.getText()
    if 'mxl' in page_text:
        mxl = bs_file.find_all('a', href=re.compile('mxl'))[0]
        formatmaxl = 'application/vnd.recordare.musicxml'
    elif 'XML' in page_text:
        mxl = bs_file.find_all('a', href=re.compile('XML'))[0]
        formatmaxl = 'application/vnd.recordare.musicxml+xml'
    elif 'xml' in page_text:
        mxl = bs_file.find_all('a', href=re.compile('xml'))[0]
        formatmaxl = 'application/vnd.recordare.musicxml+xml'
    elif 'MXL' in page_text:
        mxl = bs_file.find_all('a', href=re.compile('MXL'))[0]
        formatmaxl = 'application/vnd.recordare.musicxml'
    mxl_link = mxl['href']
    editory = mxl.parent.parent.next_sibling.next_sibling
    notes = editory.find('b', text=re.compile('notes')).next_sibling.parent.getText()

    editorx = editory.find('b', text=re.compile('Editor')).find_next_siblings('a')[0]

    editor = {'Name': editorx.getText(), 'url': 'https://www.cpdl.org' + editorx['href']}

    m_link_dict = {'Publisher': editor['Name'], 'Publisher_url': editor['url'], 'File_url': mxl_link,
                   'License': license, 'Format': formatmaxl}

    return m_link_dict, notes


def main():
    list_of_titles, md = get_list_of_titles('http://www.cpdl.org/wiki/api.php', "4-part choral music")

    print('Info retrieved')

    count_xml = 0
    count_target = 0
    count_total = 0
    count_except = 0
    dict_all = {}
    fails = []

    composers = []
    composer_dict = {}

    for title in list_of_titles:

        try:
            count_total += 1

            source = utils.check_mxl(md, title, ['MusicXML'])
            if source:

                title_str = utils.read_source(source)

                if 'CPDL copyright license' in title_str:
                    license = 'https://www0.cpdl.org/wiki/index.php/ChoralWiki:CPDL'
                else:
                    licence = 'Unknown'

                dict_file = {}

                title_file = bs(title_str, features="lxml")
                composer = find_composer(title_file)

                if composer not in composers:
                    composers.append(composer)
                    if not composer['Name'] == 'Anonymous':
                        comp_str = utils.read_source(composer['url'])
                        dict_comp = process_composer(comp_str)
                        dict_comp['Source'] = composer['url']
                        dict_comp['Title'] = composer['Name']
                        composer_dict[composer['Name']] = dict_comp

                name = find_name(title_file)

                global_description = "Composition {} by {}.".format(name.strip(), composer['Name'].strip())

                gd = "MusicXML score for {}.".format(name.strip())

                if 'Description' in title_file.getText():

                    local_description = title_file.find_all('b', text=re.compile('Description'))[
                        0].parent.get_text().replace('Description:', '').strip()

                    local_description = unicodedata.normalize('NFKC', local_description).strip()

                    description = global_description + local_description

                    gd = gd + local_description
                else:
                    description = global_description

                language = title_file.find_all('b', text=re.compile('Language'))[0].find_next_siblings()[0].string
                if language == 'None':
                    language = ''

                m_link_dict, notes = find_mxl(title_file)

                m_link_dict['Description'] = description

                m_links_out = [m_link_dict]

                description = description + notes

                dict_file['Title'] = name.strip()
                dict_file['Creator'] = composer
                dict_file['Publisher'] = editor
                dict_file['Description'] = description
                dict_file['Source'] = source
                dict_file['Contributor'] = 'https://www.upf.edu'
                dict_file['Relation'] = m_links_out
                dict_file['Language'] = 'en'

                dict_file['Subject'] = language.strip() + ' choir piece'

                dict_all[title] = dict_file

                count_xml += 1

        except Exception as e:
            count_except += 1
            print('Fail {}'.format(count_except))
            fails.append(title.encode('utf-8'))
        utils.progress(count_total, len(list_of_titles), " {} files done".format(count_xml))
    utils.write_json(dict_all, 'cpdl.json')
    utils.write_json(composer_dict, 'cpdl_composers.json')


if __name__ == '__main__':
    main()

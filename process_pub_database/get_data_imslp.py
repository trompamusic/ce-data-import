import mediawiki
import pandas as pd
from bs4 import BeautifulSoup as bs
import sys
import os,re
import json
import urllib.request
import unicodedata

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


def main():


    md = mediawiki.MediaWiki(url='https://imslp.org/api.php',rate_limit=True)
    list_of_titles = md.categorymembers("For unaccompanied chorus",results=10000,subcategories=True)[0]

    print('Info retrieved')


    count_xml = 0
    count_target = 0
    count_total = 0
    count_except = 0
    dict_text = {}
    fails = []
    dict_all = {}

    composers =[]

    composer_dict = {}




    for title in list_of_titles:
        count_total+=1

        try:
            # title = 'Et respondens Iesus dixit illis (Lange, Gregor)'

            ret_page = md.page(title)
            page_text = ret_page.html
            if ('XML' in page_text) or ('MusicXML' in page_text):
                dict_file = {}

                bs_file = bs(page_text, features="lxml")
                source = 'https:'+ret_page.url
                composer = bs_file.find_all(text = 'Composer\n')[0].parent.parent.find('td').contents[0]

                composer_name = composer.getText()

                composer_url = 'https://imslp.org' + composer['href']

                composer_name = composer_name.split(',')[1][1:]+' '+ composer_name.split(',')[0]

                composer_name = unicodedata.normalize('NFKC', composer_name).strip()

                composer = {'Name' : composer_name, 'url': composer_url}

                if composer not in composers:
                    composers.append(composer)

                    dict_comp = {}

                    pf = urllib.request.urlopen(composer['url'])
                    yourbytes = pf.read()

                    yourstr = yourbytes.decode("utf8")
                    pf.close()

                    composer_file = bs(yourstr, features="lxml")

                    if 'Wikipedia' in composer_file.getText():
                        wiki_link = composer_file.find_all('a',text = 'Wikipedia')[0]['href']
                        dict_comp['Wikipedia'] = wiki_link

                    dict_comp['Source'] = composer['url']
                    
                    dict_comp['Title'] = composer['Name']
                    
                    composer_dict[composer['Name']] = dict_comp

                name = bs_file.find_all(text = re.compile('Work Title'))[0].parent.parent.find('td').contents[0].string
                name = unicodedata.normalize('NFKC', name).strip()
                if 'Language' in bs_file.getText():
                    language = bs_file.find_all(text = re.compile('Language'))[0].parent.parent.find('td').contents[0].string

                mxl_links = [x.parent.parent for x in bs_file.find_all(text = re.compile('XML')) if x.parent.parent.name == 'a' ] 
                mxl_links_out = []

                for m_link in mxl_links:
                    m_link_dict = {}

                    mxl_link = m_link['href']
                    
                    fp = urllib.request.urlopen(mxl_link)
                    mybytes = fp.read()
                    mystr = mybytes.decode("utf8")
                    fp.close()
                    bubly = bs(mystr, features="lxml")
                    mxl_final_link = 'https://imslp.org'+bubly.find_all('a',text = re.compile('download'))[0]['href']


                    link_parent = mxl_links[0].parent.parent.parent.parent.parent


                    pubs = link_parent.find_all(text = re.compile('Arranger|Editor'))[0].parent.parent.find('td').find('a')

                    m_link_dict['Publisher'] = pubs.getText()

                    m_link_dict['Publisher_url'] = 'https://imslp.org' + pubs['href']

                    m_link_dict['File_url'] = mxl_final_link 

                    m_link_dict['License'] = 'https://imslp.org' + link_parent.find_all(text = re.compile('Copy'))[0].parent.parent.find('td').find_all('a')[0]['href']

                    m_link_dict['Format'] = 'application/zip'

                    global_desc = "MusicXML score for {} ".format(name.strip())

                    if 'Misc. Notes' in link_parent.getText():

                        pub_desc = link_parent.find_all(text = re.compile('Misc. Notes'))[0].parent.parent.getText().replace('\n','').replace('Misc. Notes','')

                        pub_desc = unicodedata.normalize('NFKC', pub_desc).strip()

                        m_link_dict['Description'] =global_desc + pub_desc

                    mxl_links_out.append(m_link_dict)




                dict_file['Title'] = name.strip()
                dict_file['Creator'] = composer
                dict_file['Description'] = "Composition {} by {}".format(name.strip(), composer['Name'].strip())
                dict_file['Source'] = source
                dict_file['Contributor'] = 'https://www.upf.edu'
                dict_file['Relation'] = mxl_links_out
                dict_file['Language'] = 'en'
                
                dict_file['Subject'] = language.replace('\n','')+' choir piece'

                dict_all[title] = dict_file
                count_xml+=1

        except Exception as e: 
            print(title.encode('utf-8'))
            print(e)
            count_except+=1
            print('Fail {}'.format(count_except))

            fails.append(title)
            
        progress(count_total, len(list_of_titles), " {} files done".format(count_xml))
    write_json(dict_all, './imslp.json')
    write_json(composer_dict, './imslp_composers.json')

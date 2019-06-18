import mediawiki
import pandas as pd
from bs4 import BeautifulSoup as bs
import sys
import os,re
import json
import urllib.request
import time
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
	md = mediawiki.MediaWiki(url='http://www.cpdl.org/wiki/api.php',rate_limit=True)
	list_of_titles = md.categorymembers("4-part choral music",results=None,subcategories=True)[0]

	print('Info retrieved')

	count_xml = 0
	count_target = 0
	count_total = 0
	count_except = 0
	dict_all = {}
	fails = []

	composers = []
	composer_dict = {}

	df  = pd.read_json('./cpdl.json')

	list_of_titles = df.keys()



	for title in list_of_titles:
		count_total+=1

		try:
			ret_page = md.page(title)
			page_text = ret_page.html

			if 'MusicXML' in page_text:
				source = ret_page.url

				fp = urllib.request.urlopen(source)
				mybytes = fp.read()

				mystr = mybytes.decode("utf8")
				fp.close()

				if 'CPDL copyright license' in mystr:
					license = 'https://www0.cpdl.org/wiki/index.php/ChoralWiki:CPDL'
				else:
					print('Liscence error')
					import pdb;pdb.set_trace()
				
				dict_file = {}
				
				bs_file = bs(mystr, features="lxml")
				compy = bs_file.find_all('b',text = re.compile('Composer|Editors'))[0].find_next_siblings('a')[0]
				compy_name = compy['title']
				compy_name = unicodedata.normalize('NFKC', compy_name).strip()
				composer = {'Name' : compy_name, 
				'url':'https://www.cpdl.org'+compy['href']}

				if composer not in composers:
					composers.append(composer)
					if not composer['Name'] == 'Anonymous':
						dict_comp = {}
						pf = urllib.request.urlopen(composer['url'])
						yourbytes = pf.read()

						yourstr = yourbytes.decode("utf8")
						pf.close()
						composer_file = bs(yourstr, features="lxml")

						if 'Biography' in yourstr:
							biop = composer_file.find_all('b',text = re.compile('Biography'))[0].parent
							bio = biop.getText().rstrip()+biop.find_next_siblings()[0].getText().strip()
							bio = bio.replace('Biography','').replace('\n','').replace(':','')
						elif 'Wikipedia article' in yourstr:
							bio = composer_file.find_all(text = re.compile('Wikipedia article'))[0].parent.find_previous_siblings('p')[0].getText().replace('\n','')
						if 'Wikipedia article' in yourstr:

							wiki_link = composer_file.find_all(text = re.compile('Wikipedia article'))[0].parent.find('a')['href']
						else: 
							wiki_link = ''

						if 'Born' in yourstr:

							born = composer_file.find_all(text = re.compile('Born'))[0].parent.next_sibling.string.replace('\n','')
						else:
							born = 'Unknown'
						if 'Died' in yourstr:
							died = composer_file.find_all(text = re.compile('Died'))[0].parent.next_sibling.string.replace('\n','')
						else:
							died = 'Unknown'




						dict_comp['Biography'] = bio
						dict_comp['Wikipedia'] = wiki_link
						dict_comp['Born'] = born
						dict_comp['Died'] = died
						dict_comp['Source'] = composer['url']
						dict_comp['Title'] = composer['Name']

						composer_dict[composer['Name']] = dict_comp

				name = bs_file.find_all(text = re.compile('Title:'))[0].parent.contents
				if len(name)>1:
					name = name[-1]
				else:
					name = bs_file.find_all('b',text = re.compile('Title:'))[0].parent.contents
					if len(name)>1:
						if name[1].isspace():
							name = name[2].string
						else:
							name = name[1].string
					else:
					    name = bs_file.find_all('b',text = re.compile('Title:'))[0].find_next_siblings()[0].string

				name = unicodedata.normalize('NFKC', name).strip()

				global_description = "Composition {} by {}".format(name.strip(), composer['Name'].strip())

				gd = "MusicXML score for {} ".format(name.strip()) 

				if 'Description' in bs_file.getText():

					local_description = bs_file.find_all('b',text = re.compile('Description'))[0].parent.get_text().replace('Description:','').strip()

					local_description = unicodedata.normalize('NFKC', local_description).strip()

					description = global_description + local_description

					gd = gd + local_description
				else:
					description = global_description

				name = name.replace('\n','')

				language = bs_file.find_all('b',text = re.compile('Language'))[0].find_next_siblings()[0].string
				if language == 'None':
					language = ''

				if 'mxl' in page_text:
					mxl = bs_file.find_all('a',href = re.compile('mxl'))[0]
					formatmaxl = 'application/vnd.recordare.musicxml'
				elif 'XML' in page_text: 
					mxl = bs_file.find_all('a',href = re.compile('XML'))[0]
					formatmaxl = 'application/vnd.recordare.musicxml+xml'
				elif 'xml' in page_text: 
					mxl = bs_file.find_all('a',href = re.compile('xml'))[0]
					formatmaxl = 'application/vnd.recordare.musicxml+xml'
				elif 'MXL' in page_text:
					mxl = bs_file.find_all('a',href = re.compile('MXL'))[0]
					formatmaxl = 'application/vnd.recordare.musicxml'
				mxl_link = mxl['href']
				editory = mxl.parent.parent.next_sibling.next_sibling
				notes = editory.find('b', text = re.compile('notes')).next_sibling.parent.getText()
				description = description + notes
				editorx = editory.find('b', text = re.compile('Editor')).find_next_siblings('a')[0]
				
				editor = {'Name': editorx.getText(), 'url': 'https://www.cpdl.org'+editorx['href']}
	
				m_link_dict = {}

				m_link_dict['Publisher'] = editor['Name']

				m_link_dict['Publisher_url'] = editor['url']

				m_link_dict['File_url'] = mxl_link

				m_link_dict['License'] = license

				m_link_dict['Description'] = gd

				m_link_dict['Format'] = formatmaxl

				m_links_out = [m_link_dict]

				dict_file['Title'] = name.strip()
				dict_file['Creator'] = composer
				dict_file['Publisher'] = editor
				dict_file['Description'] = description
				dict_file['Source'] = source
				dict_file['Contributor'] = 'https://www.upf.edu'
				dict_file['Relation'] = m_links_out
				dict_file['Language'] = 'en'
				
				dict_file['Subject'] = language.strip()+' choir piece'

				dict_all[title] = dict_file

				count_xml+=1

		except Exception as e: 
			count_except+=1

			print('Fail {}'.format(count_except))
			fails.append(title.encode('utf-8'))
		progress(count_total,len(list_of_titles), " {} files done".format(count_xml))
	write_json(dict_all, './cpdl.json')
	write_json(composer_dict, './cpdl_composers.json')

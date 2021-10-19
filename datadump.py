# Fetch full JustETF Db

# Siccome la lista è lunga e le richieste di Get sono tante, creiamo un unico file
# con tutti i dati scaricati da filtrare poi

# Questo Dump si può fare una volta al giorno, non sempre
import streamlit as sl
import mechanicalsoup
import datetime
import re
import pandas as pd
from requests import get
from io import BytesIO
import json

URL = 'https://www.justetf.com/en/etf-profile.html?isin={0}'

def process_string(s):
    s = s.strip()
    s = re.sub(' +', ' ', s)
    s = re.sub('\n', '', s)
    return s.strip()


# DIZIONARIO DEI DATI CHE CI INTERESSANO DA JUSTETF
def scrape_etf_params(response):
    global URL
    etf = {}
    etf['name'] = response.find('span', attrs={'class': 'h1'}
                                ).text.strip()

    # Potrebbero esserci ETF senza ticker ma con l'ISIN
    try:
        isin, ticker = response.find('span', attrs={'class': 'identfier'}
                                     ).findAll('span', attrs={'class': 'val'})
        # they put ',' after ISIN in the tag
        etf['isin'] = isin.text.strip()[:-1]
        etf['ticker'] = ticker.text.strip()
    except (ValueError):
        isin = response.find('span', attrs={'class': 'identfier'}
                             ).findAll('span', attrs={'class': 'val'})
        # they put ',' after ISIN in the tag
        etf['isin'] = isin.text.strip()[:-1]
        etf['ticker'] = " - "

    etf['url'] = URL.format(etf['isin'])

    etf['description'] = response.find(string=re.compile('Investment strategy')
                                       ).findNext('p').contents[0].strip()
    etf['description'] = process_string(etf['description'])

    etf['last_quote'] = ' '.join(map(lambda x: x.contents[0], response.find('div', string=re.compile('Quote')
                                                                            ).findNext('div', attrs={'class': 'val'}
                                                                                       ).findAll('span')))
    etf['last_quote_value'] = float(
        re.findall("\d+\.\d+", etf['last_quote'])[0])

    etf['one_year_low_high'] = list(response.find('div', string=re.compile("52 weeks low/high")
                                                  ).parent.div.children)
    del etf['one_year_low_high'][1]
    etf['one_year_low_high'] = re.sub(
        '[\t\n]', '', '/'.join(etf['one_year_low_high']))
    etf['one_year_low_high'] = process_string(etf['one_year_low_high'])

    one_year_low_high_values = re.findall("\d+\.\d+", etf['one_year_low_high'])
    yearly_values = []
    for value in one_year_low_high_values:
        yearly_values.append(float(value))
    etf['one_year_high'] = yearly_values[1]
    etf['one_year_low'] = yearly_values[0]

    etf['fund_size'] = re.sub('[\t\n]', '', response.find('div', string=re.compile('Fund size')
                                                          ).findPrevious('div').contents[0].strip())
    etf['fund_size'] = process_string(etf['fund_size'])
    fs_category = response.find('img', attrs={'alt': 'Fund size category', 'data-toggle': 'tooltip'}
                                )['class']
    etf['fund_size_category'] = "low cap" if fs_category[-1] == "1" else "mid cap" if fs_category[-1] == "2" else "high cap"
    etf['replication'] = re.sub('[\t\n]', '', response.find(string=re.compile("Replication")
                                                            ).parent.parent.find_next_sibling('td').text.strip())
    etf['replication'] = process_string(etf['replication'])
    etf['currency'] = response.find(string=re.compile("Fund currency")
                                    ).parent.find_next_sibling('td').text.strip()
    etf['inception_date'] = datetime.datetime.strptime(response.find(string=re.compile("Inception/ Listing Date")
                                                                     ).parent.find_next_sibling('td').text.strip(), "%d %B %Y"
                                                                     ).strftime("%Y-%m-%d")

    etf['ter'] = response.find(string=re.compile("Total expense ratio")
                               ).parent.find_previous_sibling('div').text.strip()
    etf['ter_percentage'] = float(re.findall("\d+\.\d+", etf['ter'])[0])

    etf['distribution_policy'] = response.find(string=re.compile("Distribution policy")
                                               ).parent.find_next_sibling('td').text.strip()

    try:
        one_year_distributions = response.find(string=re.compile("Dividends.*12 months")
                                               ).parent.findNext('td').find('span').text.strip()
        etf['one_year_distributions'] = float(
            re.findall("\d+\.\d+", one_year_distributions)[0])
    except:
        etf['one_year_distributions'] = 0

    etf['fund_domicile'] = response.find(string=re.compile("Fund domicile")
                                         ).parent.find_next_sibling('td').text.strip()
    # etf['listings'] = []
    # for r in response.find('h3', string=re.compile('Listings')
    #         ).parent.parent.parent.find_next_sibling().findAll('tr'):
    #     etf['listings'].append(r.td.text.strip())
    return etf

def scrape_etf(isin):
    global URL
    try:
        # with urlopen(URL.format(isin)) as connection:
            #response = BeautifulSoup(connection, 'html.parser')
        browser.open(URL.format(isin))
        response = browser.page
        return scrape_etf_params(response)
    except AttributeError as e:
        print("Fund isin '{}' not found!".format(isin))
    return None    


#TRYING TO CONNECT
browser = mechanicalsoup.StatefulBrowser(
    soup_config={'features': 'lxml'},
    raise_on_404=True,
    user_agent='MyBot/0.1: mysite.example.com/bot_info',
)
# Uncomment for a more verbose output:
# browser.set_verbose(2)

browser.open("https://www.justetf.com/en/login.html")
browser.select_form()
browser["username"] = sl.secrets['je_credentials']['username']
browser["password"] = sl.secrets['je_credentials']['password']
resp = browser.submit_selected()

page = browser.page
messages = page.find("li", class_="mega-menu__dropdown--login").find("span")
#print(messages)

print('Searching ETFs List...')
FILEPATH = sl.secrets['files_position']['full_list']
etfs = []
r = get(FILEPATH)
lista = pd.read_csv(BytesIO(r.content), header=None)
print('Downloading ETFs Data...')
for index,line in lista.iterrows():
    #print(line[0])
    etf = scrape_etf(line[0].strip())
    if etf:
        etfs.append(etf)

    else:
        print(f"ISIN not Valid: {line}")

print('Saving Data Dump...')

with open('full_etfs.json', 'w') as f:
    json.dump(etfs, f)

print('Data Mined. Enjoy!')
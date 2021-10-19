# python -m venv C:\Users\pc\MyCodebase\Streamlit\sltest
# activate
# python -m pip install --upgrade pip

# pip install streamlit
# pip install datetime
# pip install re
# pip install mechanicalsoup
# pip install requests

# pip freeze (per vedere le versioni da mettere in requirements.txt)
# streamlit run main.py
# ctrl+C
# deactivate

import streamlit as sl
import datetime
import re
import pandas as pd
from requests import get
from io import BytesIO

# @sl.cache


def locate_dump():
    datadump = sl.secrets['files_position']['datadump']
    if datadump.startswith('http'):
        r = get(datadump)
        data = pd.read_json(BytesIO(r.content))
    else:
        data = pd.read_json(datadump)
    data.index.names = ['index']
    return data


# DEFINIZIONE DEL FILTRO DA APPLICARE
def suitable(isin, data, dpolicy, scat, yold, discount, ter, dyeld, repl):
    etf = data.loc[data['isin'] == isin].to_dict('records')
    if len(etf):
        etf = etf[0]
    else:
        return False
    #print(etf)
    # Distribution Policy
    if etf['distribution_policy'] == dpolicy:
        return False

    # Capitalization
    if etf['fund_size_category'] not in scat:
        return False

    # Index Replication
    if repl=='Fisica':
        if re.match(r"[pP]hysical", etf['replication']) is None:
            return False
    else:
        if re.match(r"[pP]hysical", etf['replication']) is not None:
            return False

    # Age
    dt = datetime.timedelta(days=yold*365)  # at least 3 years old
    # dt = datetime.timedelta(days=5*365) #at least 5 years old
    # dt = datetime.timedelta(days=1*365) #at least 1 year old
    # dt = datetime.timedelta(days=10*365) #at least 10 year old
    if etf['inception_date'] > (datetime.datetime.now() - dt).strftime("%Y-%m-%d"):
        return False

    # Price
    tiles = 5  # divisione in quintili
    ntile = discount  # primo quintile == fortemente in sconto, terzo quintile == mediamente incerto, sesto quintile == va bene qualsiasi prezzo
    if etf['last_quote_value'] > (etf['one_year_low'] + ntile*(etf['one_year_high']-etf['one_year_low'])/tiles):
        return False

    # Gestione Economica
    if etf['ter_percentage'] > (ter/100):
        return False

    # Yield da Distribuzione
    if etf['distribution_policy'] == 'Distributing':
        etf['distribution_yield'] = etf['one_year_distributions']/etf['last_quote_value']
        if etf['distribution_yield'] <= (dyeld/1000):
            return False
    else:
        etf['distribution_yield'] = 0.0

    return etf


# START
sl.header('ETF Screener')
dataelab = sl.subheader('Attendi i risultati...')

data = locate_dump()

list_selection = sl.sidebar.selectbox(
    "Scegli una lista", (
        'Tutti gli Etf',
        'A Distribuzione',
        'Ad Accumulazione'
    )
)
if list_selection == 'Tutti gli Etf':
    FILEPATH = sl.secrets['files_position']['full_list']
    dpolicy=""

elif list_selection == 'A Distribuzione':
    FILEPATH = sl.secrets['files_position']['distributing_list']
    dpolicy="Accumulating"

elif list_selection == 'Ad Accumulazione':
    FILEPATH = sl.secrets['files_position']['accumulating_list']
    dpolicy="Distributing"

# FILTRI
repl = sl.sidebar.radio("Tipo di replica",["Fisica", "Swap"])
scat = sl.sidebar.multiselect("Dimensioni", ['small cap', 'mid cap', 'high cap'])
yold = sl.sidebar.slider("Anni sul Mercato",0,30)
discount = sl.sidebar.slider("Categoria Sconto",6,1)
ter = sl.sidebar.slider("Total Expense Ratio ‰ massimo",1,100)
dyeld = sl.sidebar.slider("Yield da Distribuzione ‰ minimo",1,200)

# ELABORAZIONE
screened = []
r = get(FILEPATH)
lista = pd.read_csv(BytesIO(r.content), header=None)
# print(lista)
for index, line in lista.iterrows():
    # print(line[0])
    etf = suitable(line[0].strip(), data, dpolicy, scat, yold, discount, ter, dyeld, repl)
    if etf:
        screened.append([
            etf['isin'],
            etf['replication'],
            etf['distribution_policy'],
            etf['distribution_yield'],
            etf['ter'],
            etf['fund_size_category'],
            etf['inception_date'],
            etf['url']
        ])
    else:
        #print(f"ISIN not Valid: {line}")
        pass

sl.subheader("ETF che rispettano il filtro")
df = pd.DataFrame(screened, columns=['Isin', 'Replica', 'Earnings Policy', 'Yield da Distribuzione','Ter', 'Dimensioni', 'Data Emissione', 'Link'])
dataelab.text('Attendi i risultati... Fatto!')
sl.dataframe(df)

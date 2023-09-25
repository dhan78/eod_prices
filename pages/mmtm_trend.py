import pathlib
import pandas as pd
from bs4 import BeautifulSoup
import requests

from utils.pc_utils import DB

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
db=DB(db_file=DATA_PATH.joinpath('data_store.sqlite'))

url=r'https://etfdb.com/etf/MMTM/#holdings'
page = requests.get(url)
soup = BeautifulSoup(page.text, 'html.parser')
as_of_date = soup.findAll(class_='date-modified')[-1].string
pg=pd.read_html(url)
df=pg[4]
df['% Assets % Assets']=df['% Assets % Assets'].str.replace('%','')

db.store_momentum_data(p_df=df, p_load_dt=as_of_date)
print('Saved MMTM data')

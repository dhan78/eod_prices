from pc_utils import get_headers
import pandas as pd
import requests
url = 'https://api.nasdaq.com/api/quote/TSLA/option-chain?assetclass=stocks&limit=6000&fromdate=all&todate=all&excode=oprac&callput=callput&money=all&type=all'
res = requests.get(url,headers=get_headers())
import json
df = pd.DataFrame(json.loads(res.text)['data']['table']['rows'])
import numpy as np
df['expirygroup'].replace('',np.nan, inplace=True)
df['expirygroup'].ffill(inplace=True)
df['drillDownURL']=df['drillDownURL'].apply(lambda x : f'https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@{x[59:] if x else x}&chscale=6m&chwid=700&chhig=300')

num_of_expirydts=len(sorted(df.expirygroup.unique()))
print ('finished')
char_url = "https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@TSLA%20%20220916C01800000&chscale=6m&chwid=700&chhig=300"

def get_evenly_divided_values(value_to_be_distributed, times):
    return [value_to_be_distributed // times + int(x < value_to_be_distributed % times) for x in range(times)]
green_range = get_evenly_divided_values(255,num_of_expirydts)
dict_color=dict(zip(sorted(df.expirygroup.unique()),np.cumsum(green_range)))


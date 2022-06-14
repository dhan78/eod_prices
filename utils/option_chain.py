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
print ('finished')
char_url = "https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@TSLA%20%20220916C01800000&chscale=6m&chwid=700&chhig=300"

import requests
from functools import reduce
import pandas as pd
def concatenate_json(json_obj_1, json_obj_2):
    items = json_obj_1['features'] + json_obj_2['features']
    return {'features':items}


df_main = pd.DataFrame()
# FEMA COUNTY LIST
# url = 'https://hazards.fema.gov/gis/nfhl/rest/services/MapSearch/MapSearch_v5/MapServer/0/query'
params = {
'f': 'json'
,'where': '1=1'
,'returnGeometry': 'false'
,'spatialRel': 'esriSpatialRelIntersects'
,'geometry': {"xmin":-9523688.770721475,"ymin":2917295.6124929907,"xmax":-8624789.318088042,"ymax":3664544.0010086754,"spatialReference":{"wkid":102100}}
,'geometryType': 'esriGeometryEnvelope'
,'inSR': '102100'
,'outFields': '*'
,'orderByFields': 'OBJECTID ASC'
,'outSR': '102100'
,'resultOffset': '7008'
,'resultRecordCount': '1000'
}
# r = requests.get(url,params=params)
# df = pd.DataFrame.from_records(r.json()['features'],)
# df_main = df.attributes.apply(pd.Series)
# record = 1000
# json_list=[]
# while r.json().get('exceededTransferLimit'):
#     df = pd.DataFrame.from_records(r.json()['features'],)
#     df_main.append(df.attributes.apply(pd.Series))
#     record += 1000
#     params['resultOffset'] = str(record)
#     print (f'Downloading at record -> {record}')
#     r = requests.get(url, params=params)
#
# print ('Completed')


# FEMA STATE to COUNTY LIST
url = 'https://hazards.fema.gov//gis/nfhl/rest/services/FIRMette/NFHLREST_FIRMette/MapServer/4/query'
r = requests.get(url,params=params)
df = pd.DataFrame.from_records(r.json()['features'],)
df_main = df.attributes.apply(pd.Series)
record = 1000
json_list=[]
while r.json().get('exceededTransferLimit'):
    df = pd.DataFrame.from_records(r.json()['features'],)
    df_main = df_main.append(df.attributes.apply(pd.Series))
    record += 1000
    params['resultOffset'] = str(record)
    print (f'Downloading at record -> {record}')
    r = requests.get(url, params=params)

print ('Completed')

''' 
# download FIPS -> State mapping from
# https://www.nrcs.usda.gov/wps/portal/nrcs/detail/?cid=nrcs143_013696 
dict_state_fips = dict(zip(df_state.FIPS, df_state['Postal Code']))
df_main['STATE_CODE']=df_main['ST_FIPS'].astype(int).map(dict_state_fips)
'''
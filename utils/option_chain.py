from pc_utils import get_headers
import pandas as pd
import html as html_orig
import requests
url = 'https://api.nasdaq.com/api/quote/TSLA/option-chain?assetclass=stocks&limit=6000&fromdate=all&todate=all&excode=oprac&callput=callput&money=all&type=all'
res = requests.get(url,headers=get_headers())
import json
df = pd.DataFrame(json.loads(res.text)['data']['table']['rows'])
import numpy as np
def convert_dt_to_str(p_dt_list):
    return [f"{pd.to_datetime(dt).strftime('%b %d %Y')}" for dt in p_dt_list]

df['expirygroup'].replace('',np.nan, inplace=True)
df['expirygroup'].ffill(inplace=True)
df['expirygroup']=pd.to_datetime(df.expirygroup)
df['expirygroup']=convert_dt_to_str(df.expirygroup.values)

df['drillDownURL']=df['drillDownURL'].apply(lambda x : f'https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@{x[59:] if x else x}&chscale=6m&chwid=700&chhig=300')
df.drillDownURL = df.drillDownURL.str.replace('--','  ').values





num_of_expirydts=len(sorted(df.expirygroup.unique()))
print ('finished')
char_url = "https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@TSLA%20%20220916C01800000&chscale=6m&chwid=700&chhig=300"

def get_evenly_divided_values(value_to_be_distributed, times):
    return [value_to_be_distributed // times + int(x < value_to_be_distributed % times) for x in range(times)]
green_range = get_evenly_divided_values(255,num_of_expirydts)

dict_color=dict(zip(df.expirygroup.unique(), np.cumsum(green_range)))
df['color']=df.expirygroup.map(dict_color)

df[df.filter(regex='c_|p_|strike').columns] = df.filter(regex='c_|p_|strike').\
    apply(pd.to_numeric,errors='coerce')
df=df[df.strike>600].copy()

import plotly.graph_objects as go

fig=go.Figure()
for expirydt, df_expiry in df.groupby('expirygroup' )[['strike','c_Last','color']]:
    fig.add_trace(
                    go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_Last.values, name=expirydt,
                               mode='lines', line_shape='spline', marker_color='rgb(0,300,0)', opacity=.7,
                               line=dict(color=f'rgb(0,{dict_color.get(expirydt)},0)', width=1, )))

# fig.update_layout( xaxis_tickfont_size=14,
#             height=600, width=1900,
#             showlegend=True,
#             hovermode='x',
#                               xaxis=dict(
#                                   tickmode='array',
#                                   # tickvals=df.strike.unique()
#                                   ),
#                               )
# fig.layout.update(dict(yaxis=dict(range=[0,df.strike.max()])))

fig.update_layout( xaxis_tickfont_size=14,
            height=600, width=1900,
            showlegend=True,)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State

app = Dash(__name__, external_stylesheets=external_stylesheets)
import dash_bootstrap_components as dbc

app.layout = html.Div([
    html.Div([
        dcc.Link(children="Show Option History",href='url',id='url',target='_blank'),
        dcc.Graph(
            id='basic-interactions',
            figure=fig
        )
    ], className='eight columns'),

])
def toggle_modal2(is_open):
    return not is_open

@app.callback(
    Output('url', 'children'),Output('url', 'href'),
    Input('basic-interactions', 'clickData'),
    prevent_initial_call=True
)
def display_click_data(clickData):
    curveNumber = clickData['points'][0]['curveNumber']
    strike = clickData['points'][0]['x']
    expirygroup=fig.data[curveNumber].name
    point_mask = (df.expirygroup==expirygroup)&(df.strike==strike)
    drillDownURL=df.loc[point_mask]['drillDownURL'].values[0]
    return f'Show Option History {strike},[{expirygroup}]', drillDownURL

if __name__ == '__main__':
    app.run_server(debug=True, host = '0.0.0.0', port=9900)


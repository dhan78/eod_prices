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


df['expirygroup']=pd.to_datetime(df.expirygroup)
df.strike = df.strike.astype(float)

import plotly.graph_objects as go

fig=go.Figure()
fig.update_layout( xaxis_tickfont_size=14,
            height=600, width=1900,
            showlegend=True,
            hovermode='x',
                              xaxis=dict(
                                  tickmode='array',
                                  tickvals=df.expirygroup.unique()),

                              )
fig.layout.update(dict(yaxis=dict(range=[0,df.strike.max()])))
# data=[go.Mesh3d(x=(70*np.random.randn(N)),
#                    y=(55*np.random.randn(N)),
#                    z=(40*np.random.randn(N)),
#                    opacity=0.5,
#                    color='rgba(244,22,100,0.6)'
#                   )]

df[df.filter(regex='c_|p_|strike').columns] = df.filter(regex='c_|p_|strike').apply(pd.to_numeric,
                                                                                            errors='coerce')
fig = go.Figure(data = [go.Mesh3d(z=df.expirygroup.values, x = df.strike.values , y=df.c_Last.values ,opacity=0.5,
)])
fig.update_layout( xaxis_tickfont_size=14,
            height=600, width=1900,
            showlegend=True,)
N = 70

# fig = go.Figure(data=[go.Mesh3d(x=(70*np.random.randn(N)),
#                    y=(55*np.random.randn(N)),
#                    z=(40*np.random.randn(N)),
#                    opacity=0.5,
#                    color='rgba(244,22,100,0.6)'
#                   )])

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(
        id='basic-interactions',
        figure=fig
    ),
    html.Div([
        dcc.Markdown("""
        **Click Data**

        Click on points in the graph.
    """),
        html.Pre(id='click-data', style=styles['pre']),
    ], className='three columns'),

])

@app.callback(
    Output('click-data', 'children'),
    Input('basic-interactions', 'clickData'))
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)

if __name__ == '__main__':
    app.run_server(debug=True, port=9900)


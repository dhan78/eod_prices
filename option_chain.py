import base64
import sys
# sys.path.insert(0, '')
from utils.pc_utils import Nasdaq_Leap
import dash_bootstrap_components as dbc
import pandas as pd
import html as html_orig
import requests
import json
import plotly.graph_objects as go
import numpy as np


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
import dash
from dash import Dash, dcc, html, callback
from dash.dependencies import Input, Output, State

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dash.register_page(__name__, path='/display_option_chain',
                        title = 'LEAP Options Dashboard',
                        name = 'LEAP Dashboard')

NL = Nasdaq_Leap()
fig = NL.buil_leap_fig()

app.layout=dbc.Container([
    dbc.Row([dbc.Col([
              html.H1(children="Option History",className='fs-3'),
              dcc.Loading(html.Img(id='chart_id',className='shadow')),
              html.P(children="Show Option History",id='chart_title'),
              dcc.Interval(
                    id='interval-component',
                    interval= 15*60 * 1000,  # 15 minute timer
                    n_intervals=0
                    )
              ],width={'size':9,'offset':3})], ),
    dbc.Row(dbc.Col([
        dcc.Loading(dcc.Graph(
            id='basic-interactions',
            figure=fig,
            className='shadow')),
        ], )),
], fluid=True)

def toggle_modal2(is_open):
    return not is_open

@dash.callback(
    Output('chart_title','children'),Output('chart_id', 'src'),
    Input('basic-interactions', 'clickData'),
    prevent_initial_call=True
)
def display_click_data(clickData):
    curveNumber = clickData['points'][0]['curveNumber']
    strike = clickData['points'][0]['x']
    expirygroup=fig.data[curveNumber].name
    point_mask = (NL.df.expirygroup==expirygroup)&(NL.df.strike==strike)
    drillDownURL=NL.df.loc[point_mask]['drillDownURL'].values[0]
    encoded_image = base64.b64encode(requests.get(drillDownURL).content)
    return f'Show Option History ${strike:,.0f} , [{expirygroup}]', 'data:image/png;base64,{}'.format(encoded_image.decode())

@dash.callback(
    Output('basic-interactions','figure'),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)
def refresh_nasdaq_prices(n_intervals):
    return NL.buil_leap_fig()

if __name__ == '__main__':
    # pass
    app.run_server(debug=True, host = '0.0.0.0', port=9900)


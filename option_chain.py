import base64
import sys
sys.path.insert(0, '')
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

app = Dash(__name__, external_stylesheets=external_stylesheets)
dash.register_page(__name__)
NL = Nasdaq_Leap()
fig = NL.buil_leap_fig()
app.layout = html.Div([
    dcc.Interval(
        id='interval-component',
        interval= 15*60 * 1000,  # 15 minute timer
        n_intervals=0
    ),

    dbc.Row(html.Div([
              dcc.Loading(html.Img(id='chart_id',)),
              html.P(children="Show Option History",id='chart_title'),
              ],className='six columns')),
    dbc.Row(html.Div([
        dcc.Loading(dcc.Graph(
            id='basic-interactions',
            figure=fig
        ))
    ], className='six columns')),

])
def toggle_modal2(is_open):
    return not is_open

@callback(
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

@callback(
    Output('basic-interactions','figure'),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)
def refresh_nasdaq_prices(n_intervals):
    return NL.buil_leap_fig()

if __name__ == '__main__':
    # pass
    app.run_server(debug=True, host = '0.0.0.0', port=9900)


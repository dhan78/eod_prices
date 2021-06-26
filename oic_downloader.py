import os
from datetime import datetime

import requests
import pandas as pd
import sqlite3
from sqlite3 import Error


import plotly.graph_objects as go  # or plotly.express as px

fig = go.Figure()  # or any Plotly Express function e.g. px.bar(...)
# fig.add_trace( ... )
# fig.update_layout( ... )

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def store_data(p_df, p_load_dt):
    # import pdb; pdb.set_trace()
    p_df['load_dt'] = p_load_dt
    insert_qry = ' insert or replace into tsla_nasdaq (' + ','.join(p_df.columns) + ') values ('+str('?,'*len(p_df.columns))[:-1] +') '
    conn = create_connection(os.getcwd()+'/data_store.sqlite')
    conn.executemany(insert_qry, p_df.to_records(index=False))
    conn.commit()

def oic_api_call():
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    url = 'https://api.nasdaq.com/api/quote/TSLA/option-chain?assetclass=stocks&limit=600&fromdate=2021-06-20&todate=2021-09-30&excode=oprac&callput=callput&money=at&type=all'
    response = requests.get(url, headers=headers)
    # rws = response.json()['data']['rows']

    load_dt = datetime.today().strftime('%Y-%m-%d')

    df = df = pd.DataFrame.from_dict(response.json()['data']['table']['rows'])
    df['expirygroup'] = df['expirygroup'].apply(lambda x: pd.to_datetime(x))
    df['expirygroup'].ffill(axis=0, inplace=True)
    df.dropna(inplace=True)
    df['load_dt'] = datetime.today().strftime('%Y-%m-%d')
    store_data(p_df=df, p_load_dt=load_dt)
    return df


def get_charts():
    df = oic_api_call()

    num_or_charts = len(df.expirygroup.unique())

    fig = make_subplots(rows=num_or_charts, cols=1, vertical_spacing=0.03)

    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        expirydt = expiry[0]
        df_expiry = expiry[1]
        df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.c_Openinterest.values,
                                name='Call Open Interest',
                                marker_color='rgb(0,128,0)'
                                ), row=i + 1, col=1)
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.p_Openinterest.values,
                                name='Put Open Interest',
                                marker_color='rgb(200, 0, 0)'
                                ), row=i + 1, col=1)
        #Call Volume
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.c_Volume.values,
                                name='Call Volume',
                                marker_color='rgb(0,300,0)',
                                opacity=.1
                                ), row=i + 1, col=1)
        #Put Volume
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.p_Volume.values,
                                name='Put Volume',
                                marker_color='rgb(300,0,0)',
                                opacity=.1
                                ), row=i + 1, col=1)


    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        fig.update_xaxes(row=i + 1, col=1, dtick=2.5, tickangle=-90)
        fig.update_yaxes(title_text=expiry[0].strftime('%B-%d-%Y'), range=[100, 11000], row=i + 1, col=1)
        # xaxis = dict(dtick=2.5, tickangle=-90),

    fig.update_layout(
        title='Put Call Open Interest',
        xaxis_tickfont_size=14,
        height=1800, width=1500,
        showlegend=False,
        # yaxis=dict(
        #     title='Open Interest',
        #     titlefont_size=16,
        #     tickfont_size=14,
        #     range=[100,10000]
        # ),
        # xaxis=dict(dtick=2.5,tickangle=-90),
        # legend=dict(
        #     x=0,
        #     y=1.0,
        #     bgcolor='rgba(255, 255, 255, 0)',
        #     bordercolor='rgba(255, 255, 255, 0)'
        # ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )
    return fig


app = dash.Dash()
fig = get_charts()

app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True, host='0.0.0.0')  # Turn off reloader if inside Jupyter

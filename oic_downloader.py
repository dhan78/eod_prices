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
from dash.dependencies import Input, Output, State
import simplejson as json
import re


import dateutil.parser as dparse
from datetime import timedelta

next_friday = dparse.parse("Friday")
one_week = timedelta(days=7)
weekly_expiry_target = next_friday + one_week * 6


headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}


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
    load_dt = datetime.today().strftime('%Y-%m-%d')
    weekly_expiry_end=weekly_expiry_target.strftime('%Y-%m-%d')

    url = f'https://api.nasdaq.com/api/quote/TSLA/option-chain?assetclass=stocks&limit=600&fromdate={load_dt}&todate={weekly_expiry_end}&excode=oprac&callput=callput&money=at&type=all'
    response = requests.get(url, headers=headers)
    # rws = response.json()['data']['rows']

    df = df = pd.DataFrame.from_dict(response.json()['data']['table']['rows'])
    df['expirygroup'] = df['expirygroup'].apply(lambda x: pd.to_datetime(x))
    df['expirygroup'].ffill(axis=0, inplace=True)
    df.dropna(inplace=True)
    df['load_dt'] = datetime.today().strftime('%Y-%m-%d')
    store_data(p_df=df, p_load_dt=load_dt)
    return df

def get_lastSalePrice():
    url = 'https://api.nasdaq.com/api/quote/TSLA/info?assetclass=stocks'
    response = requests.get(url, headers=headers)
    lastSalePrice=response.json()['data']['primaryData']['lastSalePrice']
    float(re.findall("\d+\.\d+", lastSalePrice)[0])
    return lastSalePrice


def get_charts(current_price):
    df = oic_api_call()

    num_or_charts = len(df.expirygroup.unique())

    fig = make_subplots(rows=num_or_charts, cols=2, vertical_spacing=0.03)

    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        expirydt = expiry[0].strftime('%B-%d-%Y')
        df_expiry = expiry[1]
        df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
        # Call Open Interest
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.c_Openinterest.values,
                                name='Call Open Interest_'+expirydt,
                                marker_color='rgb(0,128,0)',
                                opacity=.8
                                ), row=i + 1, col=1)
        # Put Open Interest
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.p_Openinterest.values,
                                name='Put Open Interest_'+expirydt,
                                marker_color='rgb(225, 0, 0)',
                                opacity=.8
                                ), row=i + 1, col=1)
        #Call Volume
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.c_Volume.values,
                                name='Call Volume_'+expirydt,
                                marker_color='rgb(0,300,0)',
                                opacity=.3
                                ), row=i + 1, col=1)
        #Put Volume
        fig.append_trace(go.Bar(x=df_expiry.strike.values,
                                y=df_expiry.p_Volume.values,
                                name='Put Volume_'+expirydt,
                                marker_color='rgb(300,0,0)',
                                opacity=.3
                                ), row=i + 1, col=1)
        # Current Price
        fig.append_trace(go.Scatter(
            x=[current_price],
            y=[5000],
            text=[str(current_price)],
            name="LastTradePrice_"+expirydt,
            mode="lines+markers+text",
            opacity=0.7,
            textfont=dict(
                family="sans serif",
                size=12,
                color="blue"
            )
        ), row=i + 1, col=1)

    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        fig.update_xaxes(row=i + 1, col=1, dtick=2.5, tickangle=-90)
        fig.update_yaxes(title_text=expiry[0].strftime('%B-%d-%Y'), range=[0, 12000], row=i + 1, col=1)

    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        expirydt = expiry[0].strftime('%B-%d-%Y')
        df_expiry = expiry[1]
        df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
        df_expiry.sort_values(by=['strike'],inplace=True)
        # Call price Change
        fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.c_Change.values,name='Call Change_'+expirydt,marker_color='rgb(0,150,0)',opacity=.5), row=i + 1, col=2)
        # Put Price Change
        fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.p_Change.values,name='Put Change_'+expirydt,marker_color='rgb(255,0,0)',opacity=.5), row=i + 1, col=2)
        # Call prices
        fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_Last.values,text=df_expiry.c_Last.values, mode='lines',line_shape='spline',name='Call price_'+expirydt,marker_color='rgb(0,150,0)',opacity=.5), row=i + 1, col=2)
        # Put prices
        fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_Last.values,text=df_expiry.c_Last.values, mode='lines',line_shape='spline',name='Put price_'+expirydt,marker_color='rgb(255,0,0)',opacity=.5), row=i + 1, col=2)
        # Current price
        fig.append_trace(go.Scatter(
            x=[current_price],
            y=[20],
            text=[str(current_price)],
            name="LastTradePrice_"+expirydt,
            mode="lines+markers+text",
            opacity=0.7,
            textfont=dict(
                family="sans serif",
                size=12,
                color="blue"
            )
        ), row=i + 1, col=2)


        # # Call price Change
        # df_expiry['c_Prev']=df_expiry.c_Last-df_expiry.c_Change
        # df_expiry['c_xy'] = df_expiry.strike.astype(str) + ',' + df_expiry.c_Last.astype(str)
        # df_expiry['c_axy'] = df_expiry.strike.astype(str) + ',' + (df_expiry.c_Last - df_expiry.c_Change).astype(str)
        # # Put price Change
        # df_expiry['p_Prev'] = df_expiry.p_Last - df_expiry.p_Change
        # df_expiry['p_xy'] = df_expiry.strike.astype(str) + ',' + df_expiry.p_Last.astype(str)
        # df_expiry['p_axy'] = df_expiry.strike.astype(str) + ',' + (df_expiry.p_Last - df_expiry.p_Change).astype(str)
    #
    #     fig.add_trace(go.Scatter(x=df_expiry.strike, y=df_expiry.c_Prev, fill='tozeroy',  mode='none',name='C_previous'), row=i+1, col=2)
    #     fig.add_trace(go.Scatter(x=df_expiry.strike, y=df_expiry.c_Last, fill='tonexty',  mode='none',name='C_current'), row=i+1, col=2)
    #
    #     fig.add_trace(go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_Prev.values, fill='tozeroy', mode='none',name='P_previous'), row=i+1, col=2)
    #     fig.add_trace(go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_Last.values, fill='tonexty', mode='none',name='P_current'), row=i+1, col=2)
    #
    for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
        fig.update_xaxes(row=i + 1, col=2, dtick=2.5, tickangle=-90)
        fig.update_yaxes(title_text=expiry[0].strftime('%B-%d-%Y'), range=[-20, 60], row=i + 1, col=2)

        # df_expiry.set_index('strike',inplace=True)
        # for c_xy, c_axy in zip(df_expiry['c_xy'],df_expiry['c_axy']):
        #     fig.add_trace(x=df_expiry.strike,y=df_expiry.c_Last,fill='tozeroy',mode='none')
    #         fig.add_annotation(
    #             x=c_xy.split(',')[0],  # arrows' head
    #             y=c_xy.split(',')[1],  # arrows' head
    #             ax=c_axy.split(',')[0],  # arrows' tail
    #             ay=c_axy.split(',')[1],  # arrows' tail
    #             xref='x2',
    #             yref='y2',
    #             # axref='x',
    #             # ayref='y',
    #             text='',  # if you want only the arrow
    #             showarrow=True,
    #             arrowhead=3,
    #             arrowsize=1,
    #             arrowwidth=1,
    #             arrowcolor='black'
    #         )

        # fig.append_trace(go.Bar(x=df_expiry.strike.values,
        #                         y=df_expiry.c_Change.values,
        #                         name='Call price Change',
        #                         marker_color='rgb(0,128,0)'
        #                         ), row=i + 1, col=2)
        # # Put price Change
        # fig.append_trace(go.Bar(x=df_expiry.strike.values,
        #                         y=df_expiry.p_Change.values,
        #                         name='Put price Change',
        #                         marker_color='rgb(200, 0, 0)'
        #                         ), row=i + 1, col=2)




    fig.update_layout(
        title='Put Call Open Interest',
        xaxis_tickfont_size=14,
        height=1800, width=1900,
        showlegend=False,
        # yaxis=dict(
        #     title='Open Interest',
        #     titlefont_size=16,
        #     tickfont_size=14,
        #     range=[100,10000]
        # ),
        # xaxis=dict(dtick=2.5,tickangle=-90),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )
    return fig


app = dash.Dash()
current_price = get_lastSalePrice()
fig = get_charts(current_price)

app.layout = html.Div([
    dcc.Graph(id='graph',figure=fig),
    html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'})
])


@app.callback(
    Output('textarea-example-output', 'children'),
    [Input('graph', 'clickData')],
    [State('graph','figure')])
def display_click_data(clickData,figure):
     try:
        curveNum = clickData['points'][0]['curveNumber']
        clickData['points'][0]['curveName']= figure['data'][curveNum]['name']
     except:
        pass

     return json.dumps(clickData, indent=2)


app.run_server(debug=True, host='0.0.0.0')  # Turn off reloader if inside Jupyter

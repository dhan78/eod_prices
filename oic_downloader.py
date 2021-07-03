import os
from datetime import datetime
import random

import requests
import pandas as pd
import sqlite3
from sqlite3 import Error
import datetime as dt
import yfinance as yf
import numpy as np


import plotly.graph_objects as go  # or plotly.express as px

fig = go.Figure()  # or any Plotly Express function e.g. px.bar(...)
# fig.add_trace( ... )
# fig.update_layout( ... )

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import simplejson as json
import re
import requests_cache

def get_yahoo_session():
    session = requests_cache.CachedSession('yfinance.cache')
    session.headers['User-agent'] = 'my-x1carbon/1.02' + str(random.random())
    return session


import dateutil.parser as dparse
from datetime import timedelta

next_friday = dparse.parse("Friday")
one_week = timedelta(days=7)
weekly_expiry_target = next_friday + one_week * 6


def get_headers():
    return {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.'+ str(random.random())+' Safari/537.36'}

def isNowInTimePeriod(startTime, endTime, nowTime):
    if startTime < endTime:
        return nowTime >= startTime and nowTime <= endTime
    else:
        #Over midnight:
        return nowTime >= startTime or nowTime <= endTime
class DB():
    def __init__(self,db_file):
        self.db_file=db_file

    def create_connection(self,db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)
        return conn

    def store_data(self,p_df, p_load_dt):
        # import pdb; pdb.set_trace()
        p_df['load_dt'] = p_load_dt
        insert_qry = ' insert or ignore into tsla_nasdaq (' + ','.join(p_df.columns) + ') values ('+str('?,'*len(p_df.columns))[:-1] +') '
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        DB_PATH = os.path.join(PROJECT_ROOT, self.db_file)
        conn = self.create_connection(DB_PATH)
        conn.executemany(insert_qry, p_df.to_records(index=False))
        conn.commit()

    def query_data(self,p_load_dt):
        sql_str = ''' select *
        from tsla_nasdaq where
        load_dt = (select load_dt from tsla_nasdaq order by load_dt desc limit 1)
        and load_tm = (select max(load_tm)
        from tsla_nasdaq where
        load_dt = (select load_dt from tsla_nasdaq order by load_dt desc limit 1)) '''

        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        DB_PATH = os.path.join(PROJECT_ROOT, self.db_file)
        conn = self.create_connection(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql_str)
        ret_rows = cur.fetchall()
        return ret_rows



class YahooFinance():
    def __init__(self,ticker,num_of_weeks):
        self.ticker,self.num_of_weeks = ticker,num_of_weeks
        self.next_friday = dparse.parse("Friday")
        self.one_week = timedelta(days=7)
        self.weekly_expiry = [next_friday + one_week * i for i in range(num_of_weeks)]

    def reshape_options_for_chart(self,p_df, price, p_expiry):
        # p_df = pd.concat([pd.DataFrame(p_df.calls), pd.DataFrame(p_df.puts)])
        p_df.calls.columns = ['c_' + col for col in p_df.calls.columns]
        p_df.puts.columns = ['p_' + col for col in p_df.puts.columns]
        p_df = pd.concat([pd.DataFrame(p_df.calls).set_index('c_strike'), pd.DataFrame(p_df.puts).set_index('p_strike')], axis=1)
        # p_df['put_call'] = p_df['c_contractSymbol'].apply(lambda x: x[10])
        # p_df = p_df.groupby(['strike', 'put_call'])['openInterest','volume'].sum().unstack().dropna()
        # p_df = p_df.groupby(['strike', 'put_call'])['openInterest'].sum().unstack().fillna(0.001)
        p_df = p_df.replace(0., 0.001)
        p_df = p_df.apply(pd.to_numeric, errors='coerce')
        # p_df = p_df[~p_df.isin([0., np.nan, np.inf, -np.inf]).any(1)]


        # p_df['total'] = p_df.P + p_df.C
        # p_df['p_c_ratio'] = p_df.p_volume / p_df.c_volume
        # p_df['c_p_ratio'] = p_df.c_volume / p_df.p_volume
        p_df.rename(
            columns={'c_lastPrice': 'c_Last', 'p_lastPrice': 'p_Last',
                     'c_change': 'c_Change', 'p_change': 'p_Change',
                     'c_volume': 'c_Volume', 'p_volume': 'p_Volume',
                    'c_openInterest': 'c_Openinterest', 'p_openInterest': 'p_Openinterest'
                     }
            ,inplace=True)
        p_df['expirygroup'] = p_expiry

        p_df = p_df.rename_axis('strike').reset_index().sort_values(by='strike')
        nearest_strikes = (p_df.strike < (price + 75)) & (p_df.strike > (price - 75))
        p_df = p_df[nearest_strikes]

        # p_df.index = range(len(p_df))
        return p_df  # .copy()

    def print_p_c_ratio_yf(self,p_ticker):
        tsla = yf.Ticker(self.ticker, session=get_yahoo_session())
        price = tsla.get_info()['regularMarketPrice']
        price = tsla.history().tail(1)['Close'].values[0]
        load_dt = str(yf.download(tickers='TSLA', period='1d', interval='1d').reset_index()['Date'].values[0])[
                  :10]  # YYYY-MM-DD format
        # tsla_oc = tsla.option_chain(p_date)
        df_p_c, weekly_fridays = [], []
        for i in range(0,self.num_of_weeks):
            weekly_friday = self.weekly_expiry[i].strftime('%Y-%m-%d')
            tsla_oc = tsla.option_chain(weekly_friday)
            weekly_fridays.append(weekly_friday)
            df_p_c.append(self.reshape_options_for_chart(tsla_oc, price, weekly_friday))

        return pd.concat(df_p_c)



class OptionChart():
    def __init__(self,df, name):
        self.df, self.name=df, name
        self.display_status=False
        self.c_url, self.p_url = '',''
    def set_symbol_name(self,name):
        symname=name
        ticker='@TSLA%20%20'
        top_url = '''https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol='''+ticker
        dt=pd.to_datetime(name['points'][0]['curveName'].split('_')[1]).strftime('%y%m%d')
        strike=name['points'][0]['x']
        strike_str='{:09.3F}'.format(strike).replace('.','')
        c_name=dt+'C'+strike_str
        p_name=dt+'P'+strike_str
        rest_of_url='''&chscale=1m&chtype=AreaChart'''
        c_url = c_name+rest_of_url
        p_url = p_name + rest_of_url
        self.c_url, self.p_url = top_url+c_url, top_url+p_url
    def get_symbol_name(self):
        return [self.c_url, self.p_url]


class Ticker():
    def __init__(self,ticker):
        self.ticker = ticker
        self.lastSalePrice = self.get_lastSalePrice()
        self.marketStatus = None
        self.lastDataStoreTime = None
        self.dataSource = None

    def get_lastSalePrice(self):
        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/info?assetclass=stocks'
        # url = 'https://api.nasdaq.com/api/quote/TSLA/realtime-trades?&limit=10&fromTime=00:00'
        response = requests.get(url, headers=get_headers())
        lastSalePrice = response.json()['data']['primaryData']['lastSalePrice']
        self.marketStatus = response.json()['data']['marketStatus']

        float(re.findall("\d+\.\d+", lastSalePrice)[0])
        self.lastSalePrice = lastSalePrice
        return lastSalePrice

    def oic_api_call(self):
        load_dt = datetime.today().strftime('%Y-%m-%d')
        weekly_expiry_end = weekly_expiry_target.strftime('%Y-%m-%d')

        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/option-chain?assetclass=stocks&limit=600&fromdate={load_dt}&todate={weekly_expiry_end}&excode=oprac&callput=callput&money=at&type=all'
        response = requests.get(url, headers=get_headers())
        # rws = response.json()['data']['rows']
        if response.json()['data']:
            df = pd.DataFrame.from_dict(response.json()['data']['table']['rows'])
            self.dataSource = 'Nasdaq'
        else:
            yf1 = YahooFinance(ticker=self.ticker,num_of_weeks=5)
            self.dataSource = 'Yahoo'
            return yf1.print_p_c_ratio_yf(self.ticker)


        df['expirygroup'] = df['expirygroup'].apply(lambda x: pd.to_datetime(x))
        df['expirygroup'].ffill(axis=0, inplace=True)
        df.dropna(inplace=True)
        df['load_dt'] = datetime.today().strftime('%Y-%m-%d')
        df['load_tm'] = datetime.today().strftime('%H:%M:%S')

        if self.marketStatus !='Market Closed' and isNowInTimePeriod(dt.time(9, 30), dt.time(16, 00),
                             dt.datetime.now().time()):  # Save data only during market hours
            try:
                if (datetime.today()-self.lastDataStoreTime)/60 > 5: db.store_data(p_df=df, p_load_dt=load_dt)
                self.lastDataStoreTime = datetime.today()
            except :
                pass
        return df

    def get_charts(self):
        df = self.oic_api_call()
        _ = self.get_lastSalePrice()

        if df is None: return None

        oc = OptionChart(df=df, name=None)

        num_or_charts = len(df.expirygroup.unique())

        fig = make_subplots(rows=num_or_charts, cols=2, vertical_spacing=0.03, print_grid=True)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0].strftime('%B-%d-%Y') if not isinstance(expiry[0],str) else expiry[0]
            df_expiry = expiry[1]
            df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            # Call Open Interest
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.c_Openinterest.values, name='Call Open Interest_'+expirydt, marker_color='rgb(0,128,0)',opacity=.8, width=.6), row=i + 1, col=1)
            # Put Open Interest
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.p_Openinterest.values,name='Put Open Interest_'+expirydt,marker_color='rgb(225, 0, 0)',opacity=.8, width=.6), row=i + 1, col=1)
            #Call Volume
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.c_Volume.values,name='Call Volume_'+expirydt,marker_color='rgb(0,300,0)',opacity=.4, width=.3), row=i + 1, col=1)
            #Put Volume
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.p_Volume.values,name='Put Volume_'+expirydt,marker_color='rgb(300,0,0)',opacity=.4, width=.3), row=i + 1, col=1)
            # Current Price
            fig.append_trace(go.Scatter(
                x=[self.lastSalePrice],
                y=[6000],
                text=[str(self.lastSalePrice)],
                name="LastTradePrice_"+expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    family="sans serif",
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=1)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=1, dtick=2.5, tickangle=-90)
            title_text=expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[0, 12000], row=i + 1, col=1)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            df_expiry = expiry[1]
            df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            df_expiry.sort_values(by=['strike'],inplace=True)
            df_expiry['c_%']=df_expiry.c_Change*100/(df_expiry.c_Last-df_expiry.c_Change)
            df_expiry['p_%'] = df_expiry.p_Change*100/ (df_expiry.p_Last - df_expiry.p_Change)
            df_expiry['c_1']=df_expiry.c_Last-df_expiry.c_Change
            df_expiry['p_1'] = df_expiry.p_Last - df_expiry.p_Change

            # Call price Change
            fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['c_%'].values, hovertemplate='%{y:.2f}%', name='C ' + expirydt, marker_color='rgb(0,150,0)', opacity=.3, width=.3), row=i + 1, col=2)
            # Put Price Change
            fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['p_%'].values, hovertemplate='%{y:.2f}%', name='P ' + expirydt, marker_color='rgb(255,0,0)', opacity=.3, width=.3), row=i + 1, col=2)
            # Call prices
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_Last.values, name='C '+expirydt, mode='lines',line_shape='spline',marker_color='rgb(0,128,0)',opacity=.8), row=i + 1, col=2)
            # Put prices
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_Last.values, name='P '+expirydt, mode='lines',line_shape='spline', marker_color='rgb(225,0,0)',opacity=.8), row=i + 1, col=2)
            # Call prices (t-1)
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_1.values,  name='C-1 ' + expirydt, mode ='lines',line_shape='spline',marker_color='rgb(6, 171, 39)',opacity=.8, line=dict(color='rgb(0,128,0)', width=1, dash='dot')), row=i + 1, col=2)
            # Put prices (t-1)
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_1.values,  name='P-1 ' + expirydt, mode='lines',line_shape='spline',marker_color='rgb(350,0,0)',opacity=.8,line=dict(color='rgb(255,0,0)', width=1, dash='dot')), row=i + 1, col=2)


            # Current price
            fig.append_trace(go.Scatter(
                x=[self.lastSalePrice],
                y=[50],
                text=[str(self.lastSalePrice)],
                name="LastTradePrice_"+expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    family="sans serif",
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=2)


        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=2, dtick=2.5, tickangle=-90)
            title_text=expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[-50, 60], row=i + 1, col=2) #,ticksuffix="%")




        fig.update_layout(
            title=f"Put Call Open Interest. [{self.dataSource}] @ <b>{datetime.today().strftime('%I:%M %p')}... {self.marketStatus}</b>",
            xaxis_tickfont_size=14,
            height=1800, width=1900,
            showlegend=False,
            title_font_size= 14,
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
            hovermode='x',
            barmode='group',
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            bargroupgap=0.1,  # gap between bars of the same location coordinate.
            # plot_bgcolor = 'rgb(184, 189, 234)',  # set the background colour
        )
        return fig


# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app = dash.Dash()
db=DB(db_file='data_store.sqlite')
tickr = Ticker('TSLA')
# current_price = tickr.get_lastSalePrice()
fig = tickr.get_charts()
figOption = None

app.layout = html.Div([
    # dbc.Button("Open modal", id="open", n_clicks=0),
    # dbc.Modal(
    #             [
    #                 dbc.ModalBody([html.Img(src=oc.c_url, style={"width": "25%"}),
    #                               html.Img(src=oc.p_url, style={"width": "25%"})]),
    #                 dbc.ModalFooter(
    #                     dbc.Button(
    #                         "Close", id="close", className="ml-auto", n_clicks=0
    #                     ))
    #
    #             ],
    #             id="modal",
    #             is_open=oc.display_status,
    #             size="sm",
    #             backdrop=True,
    #             fade=True,
    #             centered=True
    #             ),
    # dcc.Graph(id='optionGraph', figure=figOption),
    dcc.Graph(id='graph', figure=fig),
    dcc.Interval(
        id='interval-component',
        interval= 60 * 1000,  # in milliseconds
        n_intervals=0
    ),
    html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
])
# @app.callback(
#     Output("modal", "is_open"),
#     [Input("open", "n_clicks"), Input("close", "n_clicks")],
#     [State("modal", "is_open")],
# )
# def toggle_modal(n1, n2, is_open):
#     if n1 or n2:
#         return not is_open
#     return is_open

# @app.callback(
#     Output('modal', 'is_open'),
#     [Input('graph', 'clickData')],
#     [State('modal', 'is_open')])
# def display_option_history(clickData,is_open):
#     print(oc.p_url, oc.c_url)
#     return not is_open

@app.callback(Output('graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    # current_price = get_lastSalePrice()
    print('updating graph')
    return tickr.get_charts()

@app.callback(
    Output('textarea-example-output', 'children'),
    [Input('graph', 'clickData')],
    [State('graph','figure')])
def display_click_data(clickData,figure):
     try:
        curveNum = clickData['points'][0]['curveNumber']
        clickData['points'][0]['curveName']= figure['data'][curveNum]['name']
        # oc.set_symbol_name(clickData)
     except:
        pass

     return json.dumps(clickData, indent=2)


app.run_server(debug=True, host='0.0.0.0')  # Turn off reloader if inside Jupyter

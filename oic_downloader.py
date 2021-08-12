import os
import sys
from datetime import datetime
import random
import traceback
import requests
import pandas as pd
import sqlite3
from sqlite3 import Error
import datetime as dt
import yfinance as yf
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

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
run_dt_yyyy_mm_dd = datetime.today().strftime('%Y-%m-%d')
prev_friday=next_friday - one_week
prev_friday_yyyy_mm_dd=prev_friday.strftime('%Y-%m-%d')


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
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        self.DB_PATH = os.path.join(PROJECT_ROOT, self.db_file)
        # self.conn = self.create_connection(DB_PATH)

    def create_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.DB_PATH)
        except:
            e = sys.exc_info()[1]
            print(traceback.print_exc())
        return conn

    def store_data(self,p_df, p_load_dt):
        # import pdb; pdb.set_trace()

        try:
            conn = self.create_connection()
            p_df['load_dt'] = p_load_dt
            insert_qry = ' insert or ignore into tsla_nasdaq (' + ','.join(p_df.columns) + ') values ('+str('?,'*len(p_df.columns))[:-1] +') '
            conn.executemany(insert_qry, p_df.to_records(index=False))
            conn.commit()
        except:
            e = sys.exc_info()[1]
            print(traceback.print_exc())

    def query_spot_price(self,p_load_dt):
        sql_str = f'''select tsla_spot_price from tsla_nasdaq where load_dt = '{p_load_dt}' order by load_dt desc , load_tm desc limit 1 '''
        conn=self.create_connection()
        cur = conn.cursor()
        cur.execute(sql_str)
        ret_rows = cur.fetchall()
        ret_df = pd.DataFrame.from_dict(ret_rows)
        ret_df.columns = [description[0] for description in cur.description]
        return ret_df

    def query_data(self,p_load_dt):
        # get last row from previous working day
        sql_str = f''' select *
        from tsla_nasdaq where
        (load_dt,load_tm) = (select load_dt , load_tm from tsla_nasdaq where load_dt = '{p_load_dt}' order by load_dt desc , load_tm desc limit 1) '''
        conn=self.create_connection()
        cur = conn.cursor()
        cur.execute(sql_str)
        ret_rows = cur.fetchall()
        ret_df = pd.DataFrame.from_dict(ret_rows)
        ret_df.columns = [description[0] for description in cur.description]
        return ret_df

    def query_sql_data(self,p_sql):
        sql_str = p_sql
        conn=self.create_connection()
        cur = conn.cursor()
        cur.execute(sql_str)
        ret_rows = cur.fetchall()
        ret_df = pd.DataFrame.from_dict(ret_rows)
        ret_df.columns = [description[0] for description in cur.description]
        return ret_df



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
    def __init__(self,expiry_dt, strike):
        if isinstance(expiry_dt, pd.Series):
            self.expiry_dt = expiry_dt.values[0]
            self.strike = strike.values[0]
        else:
            self.expiry_dt = expiry_dt
            self.strike = strike

    def generate_fig(self):
        sql_qry=f'''select expiryDate, c_Last, p_Last, tsla_spot_price,  load_dt, load_tm from tsla_nasdaq where expiryDate = '{self.expiry_dt}' and strike = {self.strike} and tsla_spot_price not null order by load_dt, load_tm '''
        df_option = db.query_sql_data(sql_qry)
        df_option['dt'] = pd.to_datetime(df_option.load_dt + ' ' + df_option.load_tm)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.c_Last, mode='lines',line_shape='spline',marker_color='rgb(0,128,0)',opacity=.8))
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.p_Last, mode='lines', line_shape='spline',
                                 marker_color='rgb(128,0,0)', opacity=.8))
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.tsla_spot_price, mode='lines', line_shape='spline',
                                 marker_color='rgb(0,0,0)', opacity=.8),secondary_y=True)
        fig.update_layout(
            title=f"Put Call Price history. [{self.expiry_dt}] @ <b>{self.strike}... </b>",
            xaxis_tickfont_size=14,
            height=600, width=1900,
            hovermode='x',
            xaxis = dict(
                tickmode='array',
                tickvals=df_option.index,
                ticktext=df_option['dt'].apply(lambda x: x.strftime('%b %d %H:%M')),
                tickangle = -90,
                tickfont = dict(
                            size=10,
                            color="blue"
                            )
                        )
        )
        # fig.update_xaxes(rangebreaks=[dict(values=df_option.dt)])

        return fig

    def get_symbol_name(self):
        return [self.c_url, self.p_url]


class Ticker():
    def __init__(self,ticker):
        self.ticker = ticker
        self.lastSalePrice = self.get_lastSalePrice()
        self.marketStatus = None
        self.lastDataStoreTime = None
        self.dataSource = None
        self.df_predicted_price = pd.DataFrame()
        self.prevBusDay=self.get_prevBusDay()
        self.target_close = None
        self.target_close_lst = [self.target_close]
        self.df, self.fig = None, None
        self.dict_target={}

    def get_lastSalePrice(self): #Realtime price
        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/info?assetclass=stocks'
        # url = 'https://api.nasdaq.com/api/quote/TSLA/realtime-trades?&limit=10&fromTime=00:00'
        response = requests.get(url, headers=get_headers())
        lastSalePrice = response.json()['data']['primaryData']['lastSalePrice']
        self.marketStatus = response.json()['data']['marketStatus']

        self.lastSalePrice = float(re.findall("\d+\.\d+", lastSalePrice)[0])
        return lastSalePrice

    def get_prevBusDay(self):
        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/historical?assetclass=stocks&fromdate={prev_friday_yyyy_mm_dd}&limit=1&todate={run_dt_yyyy_mm_dd}'
        # url = 'https://api.nasdaq.com/api/quote/TSLA/realtime-trades?&limit=10&fromTime=00:00'
        response = requests.get(url, headers=get_headers())
        lastBusDay = response.json()['data']['tradesTable']['rows'][0]['date']
        self.lastBusDay_yyyy_mm_dd=pd.to_datetime(lastBusDay).strftime('%Y-%m-%d')

# prev_bus_day_closing price: https://api.nasdaq.com/api/quote/TSLA/historical?assetclass=stocks&fromdate=2021-06-06&limit=1&todate=2021-07-06

    def oic_api_call(self):
        load_dt = datetime.today().strftime('%Y-%m-%d')
        weekly_expiry_end = weekly_expiry_target.strftime('%Y-%m-%d')

        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/option-chain?assetclass=stocks&limit=800&fromdate={load_dt}&todate={weekly_expiry_end}&excode=oprac&callput=callput&money=at&type=all'
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
        if self.marketStatus =='Market Open':  # Save data only during market hours
            try:
                if (datetime.today()-self.lastDataStoreTime).seconds/60 > 15:
                    df.drop(['expirygroup','c_colour','p_colour','drillDownURL'],axis=1,inplace=True)
                    df['tsla_spot_price'] = self.lastSalePrice
                    db.store_data(p_df=df, p_load_dt=load_dt)
                    print('Saved data to file')
                    self.lastDataStoreTime = datetime.today()
            except :
                self.lastDataStoreTime = datetime.today()


        return df

    def get_charts(self):
        _ = self.get_lastSalePrice()
        df = self.oic_api_call()

        if df is None: return None

        num_or_charts = len(df.expirygroup.unique())

        fig = make_subplots(rows=num_or_charts, cols=2, vertical_spacing=0.03, horizontal_spacing=0.06,print_grid=True,specs=[[{"secondary_y": True}, {"secondary_y": True}]]*num_or_charts)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0].strftime('%B-%d-%Y') if not isinstance(expiry[0],str) else expiry[0]
            df_expiry = expiry[1]
            df_expiry.sort_values(by=['strike'], inplace=True)
            df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            df_expiry['c_p_ratio'] = df_expiry.c_Openinterest/df_expiry.p_Openinterest
            df_expiry['p_c_ratio'] = df_expiry.p_Openinterest/df_expiry.c_Openinterest
            # Call Open Interest
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.c_Openinterest.values, name='Call Open Interest_'+expirydt, marker_color='rgb(0,128,0)',opacity=.8, width=.6), row=i + 1, col=1)
            # Put Open Interest
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.p_Openinterest.values,name='Put Open Interest_'+expirydt,marker_color='rgb(225, 0, 0)',opacity=.8, width=.6), row=i + 1, col=1)
            #Call Volume
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.c_Volume.values,name='Call Volume_'+expirydt,marker_color='rgb(0,300,0)',opacity=.4, width=.3), row=i + 1, col=1)
            #Put Volume
            fig.append_trace(go.Bar(x=df_expiry.strike.values,y=df_expiry.p_Volume.values,name='Put Volume_'+expirydt,marker_color='rgb(300,0,0)',opacity=.4, width=.3), row=i + 1, col=1)
            # #Call/Put Ratio
            fig.add_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_p_ratio.values,name='c_p_Ratio'+expirydt,mode='lines',line_shape='spline',marker_color='rgb(0,300,0)',opacity=.7, line=dict(color='rgb(0,128,0)', width=1, )), row=i + 1, col=1, secondary_y=True)
            # #Put/Call Ratio
            fig.add_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_c_ratio.values,name='p_c_Ratio'+expirydt,mode='lines',line_shape='spline',marker_color='rgb(300,0,0)',opacity=.7, line=dict(color='rgb(255,0,0)', width=1, )), row=i + 1, col=1, secondary_y=True)


            # Current Price
            fig.append_trace(go.Scatter(
                x=[self.lastSalePrice],
                y=[6000],
                text=[str(self.lastSalePrice)],
                name="LastTradePrice_"+expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=1)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=1, dtick=2.5, tickangle=-90)
            title_text=expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[0, 12000], row=i + 1, col=1,secondary_y=False)
            fig.update_yaxes(range=[0, 10], row=i + 1, col=1,secondary_y=True)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            df_expiry = expiry[1]
            df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            df_expiry.sort_values(by=['strike'],inplace=True)
            df_expiry['c_%']=df_expiry.c_Change*100/(df_expiry.c_Last-df_expiry.c_Change)
            df_expiry['p_%'] = df_expiry.p_Change*100/ (df_expiry.p_Last - df_expiry.p_Change)
            df_expiry['c_1']=df_expiry.c_Last-df_expiry.c_Change
            df_expiry['p_1'] = df_expiry.p_Last - df_expiry.p_Change

            # Call price Change (Theta decay)
            #fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['c_Change'].values, hovertemplate='%{y:.2f}', name='C Decay' + expirydt, marker_color='rgb(0,150,0)', opacity=.8, width=.3), row=i + 1, col=2)
            # Put Price Change (Theta decay)
            #fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['p_Change'].values, hovertemplate='%{y:.2f}', name='P Decay' + expirydt, marker_color='rgb(255,0,0)', opacity=.8, width=.3), row=i + 1, col=2)
            # Call prices
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_Last.values, name='C '+expirydt, mode='lines',line_shape='spline',marker_color='rgb(0,128,0)',opacity=.8), row=i + 1, col=2)
            # Put prices
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_Last.values, name='P '+expirydt, mode='lines',line_shape='spline', marker_color='rgb(225,0,0)',opacity=.8), row=i + 1, col=2)
            # Call prices (t-1)
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.c_1.values,  name='C-1 ' + expirydt, mode ='lines',line_shape='spline',marker_color='rgb(6, 171, 39)',opacity=.8, line=dict(color='rgb(0,128,0)', width=1, dash='dot')), row=i + 1, col=2)
            # Put prices (t-1)
            fig.append_trace(go.Scatter(x=df_expiry.strike.values,y=df_expiry.p_1.values,  name='P-1 ' + expirydt, mode='lines',line_shape='spline',marker_color='rgb(350,0,0)',opacity=.8,line=dict(color='rgb(255,0,0)', width=1, dash='dot')), row=i + 1, col=2)




            fig.add_vline(x=self.lastSalePrice, line_dash='dash',line_color='black',line_width=.6, row=i + 1, col=2)
            # Current price
            fig.append_trace(go.Scatter(
                x=[self.lastSalePrice],
                y=[50-i*5],
                text=[str(self.lastSalePrice)],
                name="LastTradePrice_"+expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=2)


        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=2, dtick=2.5, tickangle=-90)
            title_text=expiry[0] if isinstance(expiry[0],str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[-15, 60], row=i + 1, col=2) #,ticksuffix="%")

        fig.update_layout(
            title=f"Put Call Open Interest. [{self.dataSource}] @ <b>{datetime.today().strftime('%I:%M %p')}... {self.marketStatus}</b>",
            xaxis_tickfont_size=14,
            height=1800, width=1900,
            showlegend=False,
            title_font_size= 14,
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
        #Save df & fig for future updates
        self.df, self.fig = df, fig
        self.target_close_lst = list(dict.fromkeys(self.target_close_lst)) # dedupe list
        self.predict()
        return self.fig

    def predict(self):
        if self.target_close is None: return #No need to update with predictions if no target closing price provided

        def fit_model(call_put_col_name):
            model_dataset_conditions=(df_friday.expiryDate == expiry_dt_mon_dt )& (df_friday[call_put_col_name] > 0.5)
            poly_x = poly.fit_transform(df_friday.loc[model_dataset_conditions, ['strike']]-closing_price)
            y = df_friday.loc[model_dataset_conditions, [call_put_col_name]]
            model = LinearRegression()
            model.fit(poly_x, y)
            return model


        df_friday = db.query_data(p_load_dt=prev_friday_yyyy_mm_dd)
        df_friday[['c_Last','p_Last']] = df_friday[['c_Last','p_Last']].apply(pd.to_numeric,errors='coerce')
        for i, expiry in enumerate(self.df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt_yyyy_mm_dd = expiry[0].strftime('%Y-%m-%d')

            expiry_dt_mon_dt = (expiry[0]-one_week).strftime('%b %d')
            if df_friday.loc[df_friday.expiryDate == expiry_dt_mon_dt].shape[0] < 10: continue  # new week wont have data in database

            closing_price = db.query_spot_price(p_load_dt=prev_friday_yyyy_mm_dd)
            closing_price = closing_price.values[0]

            ######################
            # Fit model using
            # X = transformed strike (strike-closing_price) : strike - closing_price
            # Y = friday closing price      : c_Last
            poly = PolynomialFeatures(degree=3)
            c_model = fit_model('c_Last')
            p_model = fit_model('p_Last')
            ######################

            strike = self.df[self.df.expirygroup == expiry[0].strftime('%Y-%m-%d')]['strike']
            new_strike = self.df[self.df.expirygroup == expiry[0].strftime('%Y-%m-%d')].strike.apply(
                lambda x: float(x) - self.target_close)
            # predict using this weeks latest strikes/expiries
            c_predicted_price=c_model.predict(poly.transform(new_strike[:,np.newaxis]))
            c_predicted_price[~np.greater(c_predicted_price, 0.1)] = 0.1
            p_predicted_price=p_model.predict(poly.transform(new_strike[:,np.newaxis]))
            p_predicted_price[~np.greater(p_predicted_price, 0.1)] = 0.1

            self.dict_target[expirydt_yyyy_mm_dd]=pd.DataFrame.from_records(np.concatenate((c_predicted_price,p_predicted_price),axis=1),columns=['c_target_closing_price','p_target_closing_price'],index=strike).reset_index()

        self.update_fig(self.dict_target)

    def update_fig(self,dict_target):
        # Price Predictions -- Start
        for i, expiry in enumerate(self.df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0] if isinstance(expiry[0], str) else expiry[0].strftime('%Y-%m-%d')
            new_targets=dict_target.get(expirydt,pd.DataFrame())
            if new_targets.shape[0]<10: continue
            self.fig.append_trace(
                go.Scatter(x=new_targets.strike.values, y=new_targets.c_target_closing_price.values, name='*[' + str(self.target_close)+']', mode='lines',
                           line_shape='spline', marker_color='rgb(41, 74, 253 )', opacity=.7, line=dict(color='rgb(41, 74, 253 )', width=1, )), row=i + 1, col=2)
            self.fig.append_trace(
                go.Scatter(x=new_targets.strike.values, y=new_targets.p_target_closing_price.values, name='*[' + str(self.target_close) + ']', mode='lines',
                           line_shape='spline', marker_color='rgb(121, 8, 3 )', opacity=.7, line=dict(color='rgb(121, 8, 3 )', width=1, )), row = i + 1, col = 2)

        return self.fig


app = dash.Dash('Foo', external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash()
db=DB(db_file='data_store.sqlite')
tickr = Ticker('TSLA')
# current_price = tickr.get_lastSalePrice()
fig = tickr.get_charts()
oc = OptionChart(None,None)
figOption = None
# {'display':'none'}
# {'display':'block'}

app.layout = html.Div([
    dcc.Input(id="target_close", type="number",debounce=True, placeholder="0"),
    html.Div(id='slider-output-container',style={'height':'20px','font-family':'Arial',
                               'font-size': '12px'}),
    html.Button('Reset Targets', id='reset-val', n_clicks=0),
    dbc.Checklist(
        options=[
            {"label": "ShowOptionHistory", "value": "showOptionHistory"},
            # {"label": "Disabled Option", "value": 3, "disabled": True},
        ],
        value=["showOptionHistory"],
        id="switches-input",
        switch=True,
    ),
    html.Div(id='option-chart-output-id',children=[dcc.Graph(id='option-chart-output', figure ={})],style={'display': 'block'}),
    dcc.Graph(id='graph', figure=fig),
    dcc.Interval(
        id='interval-component',
        interval= 30 * 1000,  # in milliseconds
        n_intervals=0
    )

])

def get_option_chart_display(p_switch_value):
    if 'showOptionHistory' in p_switch_value:
        return {'display':'block'}
    else:
        return {'display': 'none'}

@app.callback(
    [Output('graph', 'figure'),
     Output('option-chart-output', 'figure'),
     Output('slider-output-container', 'children'),
     Output('option-chart-output-id','style')],
    [Input('target_close', 'value'),
     Input('graph', 'clickData'),
     Input('interval-component', 'n_intervals'),Input('reset-val', 'n_clicks'),
     Input('switches-input','value')],
    [State('graph','figure'),State('target_close','value'),
     ],
    prevent_initial_call=True
)
def display_click_data(target_closing_price, clickData,n_intervals, n_clicks,switch_value, figure,target_close):
    tickr.target_close_lst.append(target_close)
    target_close_text = 'Target Closing Price (Modeled) : "{}"'.format(', '.join([str(i) for i in list(set(tickr.target_close_lst)) if i]))

    try:
        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'graph.clickData': # just clicking chart
            curveNum = clickData['points'][0]['curveNumber']
            clickData['points'][0]['curveName'] = figure['data'][curveNum]['name']
            df_click = pd.DataFrame(clickData['points']).dropna(subset=['curveName'])
            df_click['expiry_dt'] = df_click.curveName.apply(lambda x: pd.to_datetime(x.split()[1]).strftime('%b %d'))
            oc = OptionChart(df_click.expiry_dt,df_click.x)
            return tickr.fig,oc.generate_fig(),target_close_text, get_option_chart_display(switch_value)
        elif ctx.triggered[0]['prop_id'] == 'interval-component.n_intervals': # triggered by timer
            tickr.get_lastSalePrice()
            if tickr.marketStatus == 'Market Closed': raise dash.exceptions.PreventUpdate()

            return tickr.get_charts(),dash.no_update,target_close_text,get_option_chart_display(switch_value)
        elif ctx.triggered[0]['prop_id'] == 'target_close.value': # triggered by changing target_close
            tickr.target_close = target_close
            tickr.get_lastSalePrice()
            tickr.predict()
            return tickr.fig, dash.no_update,target_close_text, get_option_chart_display(switch_value)
        elif ctx.triggered[0]['prop_id'] == 'reset-val.n_clicks': # triggered by clicking reset button
            tickr.target_close_lst , tickr.target_close = [], None
            tickr.dict_target = {}
            target_close_text = 'Target Closing Price : "{}"'.format(
                ', '.join([str(i) for i in list(set(tickr.target_close_lst))]))
            return tickr.get_charts(), dash.no_update, target_close_text, get_option_chart_display(switch_value)
        elif ctx.triggered[0]['prop_id'] == 'switches-input.value':  # triggered by clicking reset button
            return dash.no_update, dash.no_update, dash.no_update, get_option_chart_display(switch_value)
    except:
        e = sys.exc_info()[1]
        print (traceback.print_exc())
        raise dash.exceptions.PreventUpdate
        # return fig, dash.no_update,target_close_text, dash





app.run_server(debug=True, host='0.0.0.0')  # Turn off reloader if inside Jupyter

import pathlib
from datetime import datetime
import sqlite3
import sys
import traceback
from sqlite3 import Error
import datetime as dt

#import requests_cache
# import requests_cache
# import requests_cache
import yfinance as yf
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, MinMaxScaler
import requests
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import simplejson as json
import re
#import requests_cache
import random
import pandas as pd
from enum import Enum, auto
import time

def get_yahoo_session():
    session = requests_cache.CachedSession('yfinance.cache')
    session.headers['User-agent'] = 'my-x1carbon/1.02' + str(random.random())
    return session


class OIC_State(Enum):
    IDLE = auto()
    RUNNING = auto()


import dateutil.parser as dparse
from datetime import timedelta

next_friday = dparse.parse("Friday")
next_monday = dparse.parse("Monday")
one_week = timedelta(days=7)
weekly_expiry_target = next_friday + one_week * 6
run_dt_yyyy_mm_dd = datetime.today().strftime('%Y-%m-%d')
prev_friday=next_friday - one_week
prev_monday=next_monday - one_week
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

    def query_range_data(self,p_expiry, p_load_dt_start, p_load_dt_end):
        # get last row from previous working day
        sql_str = f''' select *
        from tsla_nasdaq where expiryDate = '{p_expiry}' and
        load_dt >= '{p_load_dt_start}' and load_dt <='{p_load_dt_end}' 
        order by load_dt desc , load_tm desc '''
        conn=self.create_connection()
        cur = conn.cursor()
        cur.execute(sql_str)
        ret_rows = cur.fetchall()
        ret_df = pd.DataFrame.from_dict(ret_rows)
        ret_df.columns = [description[0] for description in cur.description]
        return ret_df


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
db=DB(db_file=DATA_PATH.joinpath('data_store.sqlite'))


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
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.c_Last, mode='lines',line_shape='spline',
                                 name=f'Call {self.strike}/{self.expiry_dt}', marker_color='rgb(0,128,0)',opacity=.5))
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.p_Last, mode='lines', line_shape='spline',
                                 name=f'Put {self.strike}/{self.expiry_dt}', marker_color='rgb(225,0,0)', opacity=.5))
        fig.add_trace(go.Scatter(x=df_option.index, y=df_option.tsla_spot_price, mode='lines', line_shape='spline',
                                 name=f'TSLA Spot', marker_color='rgb(0,0,0)', opacity=.3),secondary_y=True)

        for line in df_option.reset_index().groupby('load_dt')['index'].min():
            fig.add_vline(x=line, line_dash='dash', line_color='black', line_width=.6 )

        fig.update_layout(
            title=f"Put Call Price history. [{self.expiry_dt}] @ <b> [{self.strike}]</b> ... ",
            xaxis_tickfont_size=14,
            height=600, width=1900,
            showlegend=True,
            hovermode='x',
            xaxis = dict(
                tickmode='array',
                tickvals=df_option.index,
                ticktext=df_option['dt'].apply(lambda x: x.strftime('%b %d %H:%M')),
                tickangle = -60,
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
        self.state = OIC_State.IDLE

    def set_state(self, state:OIC_State):
        self.state = state

    def get_lastSalePrice(self): #Realtime price
        url = f'https://api.nasdaq.com/api/quote/{self.ticker}/info?assetclass=stocks'
        # url = 'https://api.nasdaq.com/api/quote/TSLA/realtime-trades?&limit=10&fromTime=00:00'
        response = requests.get(url, headers=get_headers())
        lastSalePrice = response.json()['data']['primaryData']['lastSalePrice']
        self.marketStatus = response.json()['data']['marketStatus']

        self.lastSalePrice = float(re.findall("\d+\.\d+", lastSalePrice)[0])
        return lastSalePrice

    def get_prevBusDay(self):
        try:
            url = f'https://api.nasdaq.com/api/quote/{self.ticker}/historical?assetclass=stocks&fromdate={prev_friday_yyyy_mm_dd}&limit=1&todate={run_dt_yyyy_mm_dd}'
            response = requests.get(url, headers=get_headers())
            lastBusDay = response.json()['data']['tradesTable']['rows'][0]['date']
            self.lastBusDay_yyyy_mm_dd = pd.to_datetime(lastBusDay).strftime('%Y-%m-%d')
        except Exception as e:
            url = f'https://api.nasdaq.com/api/quote/{self.ticker}/info?assetclass=stocks'
            response = requests.get(url, headers=get_headers())
            self.lastBusDay_yyyy_mm_dd = pd.to_datetime(response.json()['data']['secondaryData']['lastTradeTimestamp'].split('ON')[1]).strftime(
                '%Y-%m-%d')


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

    def get_charts(self, *args, **kwargs):
        self.set_state(OIC_State.RUNNING)

        if 'replay' not in kwargs.keys():
            _ = self.get_lastSalePrice()
            lastSalePrice = self.lastSalePrice
            df = self.oic_api_call()
        else:
            df = kwargs.get('p_df')
            lastSalePrice = kwargs.get('tsla_spot_price')

        if df is None: return None

        # convert numeric columns before manipulation.
        df[df.filter(regex='c_|p_|strike').columns] = df.filter(regex='c_|p_|strike').apply(pd.to_numeric,
                                                                                            errors='coerce')
        if kwargs.get('show_volume'):
            try:
                # run_dt_yyyy_mm_dd='2022-01-07'
                df_vol = db.query_sql_data(
                    f"with st_tm as (select min(load_tm) as tm from tsla_nasdaq where load_dt = '{run_dt_yyyy_mm_dd}')select * from st_tm, tsla_nasdaq where load_dt = '{run_dt_yyyy_mm_dd}' and load_tm = st_tm.tm")
                df_vol['p_Volume_1'] = pd.to_numeric(df_vol['p_Volume'].astype(str), errors='coerce').fillna(0)
                df_vol['c_Volume_1'] = pd.to_numeric(df_vol['c_Volume'].astype(str), errors='coerce').fillna(0)

                df = df.merge(df_vol[['expiryDate', 'strike', 'p_Volume_1', 'c_Volume_1']], left_on=['expiryDate', 'strike'],
                         right_on=['expiryDate', 'strike'], )
                df['c_Volume_1'] = df['c_Volume'] - df['c_Volume_1']
                df['p_Volume_1'] = df['p_Volume'] - df['p_Volume_1']
            except Exception as e:
                print ('Exception in show_volume section')
                print ('*'*10, e)

        if 'c_Volume_1' not in df.columns:
            df['c_Volume_1'] = df['c_Volume']
            df['p_Volume_1'] = df['p_Volume']

        num_or_charts = len(df.expirygroup.unique())

        fig = make_subplots(rows=num_or_charts, cols=2, vertical_spacing=0.03, horizontal_spacing=0.06, print_grid=True,
                            specs=[[{"secondary_y": True}, {"secondary_y": True}]] * num_or_charts)
        y_max = df.filter(regex='Openinterest').apply(pd.to_numeric, errors='coerce').max(axis=1).max()*1.1
        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0].strftime('%B-%d-%Y') if not isinstance(expiry[0], str) else expiry[0]
            df_expiry = expiry[1]
            # df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            df_expiry.sort_values(by='strike', inplace=True)
            df_expiry['c_p_ratio'] = df_expiry.c_Openinterest / df_expiry.p_Openinterest
            df_expiry['p_c_ratio'] = df_expiry.p_Openinterest / df_expiry.c_Openinterest
            custom_feature_range = (0,df_expiry[['c_Openinterest','p_Openinterest']].max().max())
            df_expiry[['c_Volume_1', 'p_Volume_1']] = MinMaxScaler(feature_range=custom_feature_range).fit_transform(
                df_expiry[['c_Volume_1', 'p_Volume_1']].values)
            # df_expiry['p_Volume_1'] = StandardScaler().fit_transform(df_expiry['p_Volume_1'].values)
            # df_expiry['c_Volume_1'] = StandardScaler().fit_transform(df_expiry['c_Volume_1'].values)

            # Call Open Interest
            fig.add_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry.c_Openinterest.values,
                                    name='Call Open Interest_' + expirydt, marker_color='rgb(0,128,0)', opacity=.8,
                                    width=.6), row=i + 1, col=1, )
            # Put Open Interest
            fig.add_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry.p_Openinterest.values,
                                    name='Put Open Interest_' + expirydt, marker_color='rgb(225, 0, 0)', opacity=.8,
                                    width=.6), row=i + 1, col=1)
            # Call Volume
            # fig.append_trace(
            #     go.Bar(x=df_expiry.strike.values, y=df_expiry.c_Volume.values, name='Call Volume_' + expirydt,
            #            marker_color='rgb(0,300,0)', opacity=.4, width=.3), row=i + 1, col=1)
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_Openinterest.values/2, mode='markers',
                           name='Call Volume_' + expirydt,
                           marker=dict(size=[z/100 for z in df_expiry.c_Volume_1.fillna(0).values],
                                       color=['rgb(6, 171, 39)'] * len(df_expiry.c_Volume.values)), opacity=.3, ),
                row=i + 1, col=1)
            # Put Volume
            # fig.append_trace(
            #     go.Bar(x=df_expiry.strike.values, y=df_expiry.p_Volume.values, name='Put Volume_' + expirydt,
            #            marker_color='rgb(300,0,0)', opacity=.4, width=.3), row=i + 1, col=1)
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_Openinterest.values/2, mode='markers',
                           name='Put Volume_' + expirydt,
                           marker=dict(size=[z/100 for z in df_expiry.p_Volume_1.fillna(0).values],
                                       color=['rgb(300,0,0)'] * len(df_expiry.c_Volume.values)), opacity=.3, ),
                row=i + 1, col=1)


            # #Call/Put Ratio
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_p_ratio.values, name='c_p_Ratio ' + expirydt,
                           mode='lines', line_shape='spline', marker_color='rgb(0,300,0)', opacity=.7,
                           line=dict(color='rgb(0,128,0)', width=1, )), row=i + 1, col=1, secondary_y=True)
            # #Put/Call Ratio
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_c_ratio.values, name='p_c_Ratio ' + expirydt,
                           mode='lines', line_shape='spline', marker_color='rgb(300,0,0)', opacity=.7,
                           line=dict(color='rgb(255,0,0)', width=1, )), row=i + 1, col=1, secondary_y=True)

            # Current Price
            fig.add_trace(go.Scatter(
                x=[lastSalePrice],
                y=[y_max * .9],
                text=[str(lastSalePrice)],
                name="LastTradePrice_" + expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=1)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=1, dtick=5, tickangle=-90)
            title_text = expiry[0] if isinstance(expiry[0], str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[0, y_max], row=i + 1, col=1, secondary_y=False)
            fig.update_yaxes(range=[0, 10], row=i + 1, col=1, secondary_y=True)
            fig.add_vline(x=lastSalePrice, line_dash='dash', line_color='black', line_width=.6, row=i + 1, col=1)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            expirydt = expiry[0] if isinstance(expiry[0], str) else expiry[0].strftime('%B-%d-%Y')
            df_expiry = expiry[1]
            df_expiry = df_expiry.filter(regex='c_|p_|strike').apply(pd.to_numeric, errors='coerce')
            df_expiry.sort_values(by=['strike'], inplace=True)
            df_expiry['c_%'] = df_expiry.c_Change * 100 / (df_expiry.c_Last - df_expiry.c_Change)
            df_expiry['p_%'] = df_expiry.p_Change * 100 / (df_expiry.p_Last - df_expiry.p_Change)
            df_expiry['c_1'] = df_expiry.c_Last - df_expiry.c_Change
            df_expiry['p_1'] = df_expiry.p_Last - df_expiry.p_Change

            # Call price Change (Theta decay)
            # fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['c_Change'].values, hovertemplate='%{y:.2f}', name='C Decay' + expirydt, marker_color='rgb(0,150,0)', opacity=.8, width=.3), row=i + 1, col=2)
            # Put Price Change (Theta decay)
            # fig.append_trace(go.Bar(x=df_expiry.strike.values, y=df_expiry['p_Change'].values, hovertemplate='%{y:.2f}', name='P Decay' + expirydt, marker_color='rgb(255,0,0)', opacity=.8, width=.3), row=i + 1, col=2)
            # Call prices
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_Last.values, name='C ' + expirydt, mode='lines',
                           line_shape='spline', marker_color='rgb(0,128,0)', opacity=.8), row=i + 1, col=2)
            # Put prices
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_Last.values, name='P ' + expirydt, mode='lines',
                           line_shape='spline', marker_color='rgb(225,0,0)', opacity=.8), row=i + 1, col=2)
            # Call prices (t-1)
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_1.values, name='C-1 ' + expirydt, mode='lines',
                           line_shape='spline', marker_color='rgb(6, 171, 39)', opacity=.8,
                           line=dict(color='rgb(0,128,0)', width=1, dash='dot')), row=i + 1, col=2)
            # Put prices (t-1)
            fig.add_trace(
                go.Scatter(x=df_expiry.strike.values, y=df_expiry.p_1.values, name='P-1 ' + expirydt, mode='lines',
                           line_shape='spline', marker_color='rgb(350,0,0)', opacity=.8,
                           line=dict(color='rgb(255,0,0)', width=1, dash='dot')), row=i + 1, col=2)

            fig.add_vline(x=lastSalePrice, line_dash='dash', line_color='black', line_width=.6, row=i + 1, col=2)
            # Current price
            fig.add_trace(go.Scatter(
                x=[lastSalePrice],
                y=[50 - i * 5],
                text=[str(lastSalePrice)],
                name="LastTradePrice_" + expirydt,
                mode="text",
                opacity=0.7,
                textfont=dict(
                    size=12,
                    color="blue"
                )
            ), row=i + 1, col=2)

        for i, expiry in enumerate(df.sort_values(by=['expirygroup']).groupby(['expirygroup'])):
            fig.update_xaxes(row=i + 1, col=2, dtick=5, tickangle=-90)
            title_text = expiry[0] if isinstance(expiry[0], str) else expiry[0].strftime('%B-%d-%Y')
            fig.update_yaxes(title_text=title_text, range=[0, 60], row=i + 1, col=2)  # ,ticksuffix="%")

        fig.update_layout(
            title=f"Put Call Open Interest. [{self.dataSource}] @ <b>{datetime.today().strftime('%I:%M %p')}... {self.marketStatus}</b>",
            xaxis_tickfont_size=12,
            height=300 * num_or_charts, width=1900,
            showlegend=False,
            title_font_size=14,
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            hovermode='x',
            barmode='group',
            # bargap=0.15,  # gap between bars of adjacent location coordinates.
            bargroupgap=0.,  # gap between bars of the same location coordinate.
            # plot_bgcolor = 'rgb(184, 189, 234)',  # set the background colour
        )
        # Save df & fig for future updates
        self.df, self.fig = df, fig
        self.target_close_lst = list(dict.fromkeys(self.target_close_lst))  # dedupe list
        self.predict()
        self.set_state(OIC_State.IDLE)
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
            self.fig.add_trace(
                go.Scatter(x=new_targets.strike.values, y=new_targets.c_target_closing_price.values, name='*[' + str(self.target_close)+']', mode='lines',
                           line_shape='spline', marker_color='rgb(41, 74, 253 )', opacity=.7, line=dict(color='rgb(41, 74, 253 )', width=1, )), row=i + 1, col=2)
            self.fig.append_trace(
                go.Scatter(x=new_targets.strike.values, y=new_targets.p_target_closing_price.values, name='*[' + str(self.target_close) + ']', mode='lines',
                           line_shape='spline', marker_color='rgb(121, 8, 3 )', opacity=.7, line=dict(color='rgb(121, 8, 3 )', width=1, )), row = i + 1, col = 2)

        return self.fig

    def create_history_fig(self,p_start_date,p_end_date):
        # prev_monday, prev_friday = dparse.parse('Monday') - one_week, dparse.parse('Friday') - one_week
        prev_monday, prev_friday = pd.to_datetime(p_start_date),pd.to_datetime(p_end_date)
        prev_friday_short = prev_friday.strftime('%b %d')
        df = db.query_range_data(p_expiry=prev_friday_short
                                 , p_load_dt_start=prev_monday
                                 , p_load_dt_end=prev_friday
                                 )
        df['expirygroup'] = pd.to_datetime('2021 ' + df.expiryDate)
        df.sort_values(by=['load_dt','load_tm'],inplace=True)
        strike_min, strike_max = df.strike.values.min(),df.strike.values.max()

        ##############################################################################
        frame_list, sliders_dict = [], {'steps': []}
        for i, dfi in df.groupby(['load_dt', 'load_tm']):
            tsla_spot_price = dfi.tsla_spot_price.values[0]
            fig_i = self.get_charts(replay=True, p_df=dfi, tsla_spot_price=tsla_spot_price)
            #     import pdb; pdb.set_trace()

            dt_time = pd.to_datetime(f'{dfi.load_dt.values[0]} {dfi.load_tm.values[0]}').strftime(
                '%m-%d, %A,  %-I:%M %p')
            fig_i['layout']['title'] = f'As of {dt_time}'
            fig_i.layout.update(dict(yaxis=dict(range=[0,50000])))
            fig_i.layout.update(dict(yaxis2=dict(range=[0, 10])))
            frame_list.append(go.Frame(data=fig_i.data, layout=fig_i.layout))
            slider_step = {"args": [
                [i[0] + i[1]],
                {"frame": {"duration": 300, "redraw": False},
                 "mode": "immediate",
                 "transition": {"duration": 300}}
            ],
                "label": i[0] + i[1],
                "method": "animate"}
            sliders_dict["steps"].append(slider_step)

        ##############################################################################
        fig = make_subplots(rows=1, cols=2, vertical_spacing=0.03, horizontal_spacing=0.06, print_grid=True,
                            specs=[[{"secondary_y": True}, {"secondary_y": True}]] * 1);
        fig.frames = frame_list
        # animation needs first frame to mimic final layout. hence the following line
        df_i = df.sort_values(by=['load_dt', 'load_tm']).groupby('load_dt').head(1)
        fig.add_traces(self.get_charts(replay=True, p_df=df_i).data);
        fig.layout = go.Layout(
            # width=1500, height=700,
            xaxis=dict(range=[strike_min, strike_max], autorange=False),
            xaxis2=dict(range=[strike_min, strike_max], autorange=False),
            yaxis=dict(range=[0, 50000], autorange=False),
            yaxis2=dict(range=[0, 10], autorange=False),
            yaxis3=dict(range=[0, 60], autorange=False),
            yaxis4=dict(range=[0, 60], autorange=False),
            title="Replay previous Week",
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(label="Play",
                              method="animate",
                              args=[None])])],

        )
        # fig["layout"]["sliders"] = [sliders_dict]
        # fig.update_layout(sliders=[sliders_dict])
        ##############################################################################

        return fig


def convert_dt_to_str(p_dt_list):
    return [f"{pd.to_datetime(dt).strftime('%b %d %Y')}" for dt in p_dt_list]

class Nasdaq_Leap():
    def __int__(self):
        self.df, self.dict_color = None, None

    def get_nasdaq_leap_option_chain(self):
        url = 'https://api.nasdaq.com/api/quote/TSLA/option-chain?assetclass=stocks&limit=6000&fromdate=all&todate=all&excode=oprac&callput=call&money=out&type=all'
        res = requests.get(url, headers=get_headers())
        df = pd.DataFrame(json.loads(res.text)['data']['table']['rows'])

        df['expirygroup'].replace('',np.nan, inplace=True)
        df['expirygroup'].ffill(inplace=True)
        df['expirygroup']=pd.to_datetime(df.expirygroup)
        df['expirygroup']=convert_dt_to_str(df.expirygroup.values)

        df['drillDownURL']=df['drillDownURL'].apply(lambda x : f'https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@{x[59:] if x else x}&chscale=6m&chwid=700&chhig=300')
        df.drillDownURL = df.drillDownURL.str.replace('--','  ').values


        num_of_expirydts=len(sorted(df.expirygroup.unique()))
        char_url = "https://app.quotemedia.com/quotetools/getChart?webmasterId=90423&symbol=@TSLA%20%20220916C01800000&chscale=6m&chwid=1000&chhig=300"

        def get_evenly_divided_values(value_to_be_distributed, times):
            return [value_to_be_distributed // times + int(x < value_to_be_distributed % times) for x in range(times)]
        green_range = get_evenly_divided_values(255,num_of_expirydts)

        dict_color=dict(zip(df.expirygroup.unique(), reversed(np.cumsum(green_range))))
        df['color']=df.expirygroup.map(dict_color)

        df[df.filter(regex='c_|p_|strike').columns] = df.filter(regex='c_|p_|strike').\
            apply(pd.to_numeric,errors='coerce')
        df=df[df.strike>600].copy()
        print (f'{get_evenly_divided_values.__name__} : finished Data Manipulation')
        self.df, self.dict_color = df, dict_color
        return self.df, self.dict_color

    def buil_leap_fig(self):

        df, dict_color = self.get_nasdaq_leap_option_chain()
        df['c_Volume_1'] = pd.to_numeric(df['c_Volume'].astype(str), errors='coerce').fillna(0)
        df['c_Openinterest'] = pd.to_numeric(df['c_Openinterest'].astype(str), errors='coerce').fillna(0)
        # StandardScaler().fit_transform(df['c_Openinterest'])
        legendrank = 1001
        spot = df.strike.min()
        fig = go.Figure()
        def marker_size_by_strike(strike,volume):
            if strike > spot*1.2:
                return max(volume / 600, 0)
            else:
                return 0

        for expirydt, df_expiry in df.groupby('expirygroup'):#[['strike', 'c_Last', 'color']]:
            legendrank = int((pd.to_datetime(expirydt,format='%b %d %Y') - pd.Timestamp.today())/np.timedelta64(1,'D'))
            fig.add_trace(
                                go.Scatter(x=df_expiry['strike'], y=df_expiry['c_Last'], name=expirydt,text=df_expiry['expirygroup'],
                                           mode='lines+markers', line_shape='spline', marker_color='rgb(0,0,255)', opacity=1.,
                                           customdata=np.stack((df_expiry['c_Openinterest'], df_expiry['c_Volume_1']),
                                                               axis=-1),
                                           # marker=dict(
                                           #     color='green',
                                           #     size=3,
                                           #     line=dict(
                                           #         color='red',
                                           #         width=1
                                           #     )),
                                           marker=dict(opacity=.3,
                                               size=[marker_size_by_strike(strike,z) for strike,z in zip(df_expiry.strike.values,df_expiry.c_Openinterest.values)],
                                               color=['green'] * len(df_expiry.c_Volume.values)),

                                        hovertemplate=
                                           "<b>%{text}</b><br><br>" +
                                           "Strike: %{x:$,.0f}<br>" +
                                           "Theta: %{y:.2f}<br>" +
                                           "Openinterest: %{customdata[0]:,.0f}<br>" +
                                           "Volume: %{customdata[1]:,.0f}<br>"
                                           ,
                                           line=dict(color=f'rgb(0,{dict_color.get(expirydt)},0)', width=1),
                                           legendrank=legendrank)
                                            )
            # fig.add_trace(
            #     go.Scatter(x=df_expiry.strike.values, y=df_expiry.c_Volume.values / 2, mode='markers',
            #                name='Call Volume_' + expirydt,
            #                marker=dict(size=[max(z / 100, 0) for z in df_expiry.c_Volume_1.fillna(0).values],
            #                            color=['rgb(6, 171, 39)'] * len(df_expiry.c_Volume.values)), opacity=.3, ))

        fig.layout.update(dict(yaxis=dict(range=[0,df.c_Last.max()])))

        fig.update_layout( xaxis_tickfont_size=14,
                    height=600, width=1900,
                    showlegend=True,
                    )
        return fig

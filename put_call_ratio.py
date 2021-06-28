# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import pdb
import re

from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import yfinance as yf
import random
import seaborn as sns

import base64
from io import BytesIO

from flask import Flask
from matplotlib.figure import Figure

import dateutil.parser as dparse
from datetime import timedelta

next_friday = dparse.parse("Friday")
one_week = timedelta(days=7)
weekly_expiry = [next_friday + one_week * i for i in range(4)]

matplotlib.use('TkAgg')

import sys
import glob, os
import time
import subprocess
import fnmatch
import numpy as np

import sqlite3
from sqlite3 import Error
from datetime import datetime

from selenium import webdriver

sns.set_theme()

import requests_cache

session = requests_cache.CachedSession('yfinance.cache')
session.headers['User-agent'] = 'my-x1carbon/1.02' + str(random.random())

# //*[@id="Col1-1-OptionContracts-Proxy"]/section/section[1]/div[2]/div/table/tbody/tr[44]
if len(sys.argv) > 1:
    ticker = sys.argv[1]
    width = float(sys.argv[2])
    p_date = sys.argv[3]

else:
    ticker = ''
    width = 50.0
    p_date = ''


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
    insert_qry = ' insert or replace into tsla_op (' + ','.join(p_df.columns) + ') values (?,?,?,?,?,?,?,?) '

    conn = create_connection(os.getcwd()+'/data_store.sqlite')
    conn.executemany(insert_qry, p_df.to_records(index=False))
    conn.commit()


def reshape_options_for_chart(p_df, price, p_expiry):
    p_df = pd.concat([pd.DataFrame(p_df.calls), pd.DataFrame(p_df.puts)])
    p_df['put_call'] = p_df['contractSymbol'].apply(lambda x: x[10])
    p_df = p_df.groupby(['strike', 'put_call'])['openInterest'].sum().unstack().dropna()
    # p_df = p_df.groupby(['strike', 'put_call'])['openInterest'].sum().unstack().fillna(0.001)
    p_df = p_df.replace(0., 0.1)
    p_df = p_df[~p_df.isin([0., np.nan, np.inf, -np.inf]).any(1)]

    p_df['total'] = p_df.P + p_df.C
    p_df['p_c_ratio'] = p_df.P / p_df.C
    p_df['c_p_ratio'] = p_df.C / p_df.P
    p_df['expiry'] = p_expiry

    p_df = p_df.reset_index().sort_values(by=['strike'])
    nearest_strikes = (p_df.strike < (price + 300)) & (p_df.strike > (price - 200))
    p_df = p_df[nearest_strikes]

    p_df.index = range(len(p_df))
    return p_df  # .copy()


def build_ax(p_df, p_ax, p_date, p_price):
    p_df['p_c_ratio'].plot(kind='line', color='r', ax=p_ax)
    p_df['c_p_ratio'].plot(kind='line', color='g', ax=p_ax)
    p_df['P'].plot(kind='bar', ax=p_ax, color='r', alpha=.4, secondary_y=True)
    p_df['C'].plot(kind='bar', ax=p_ax, color='g', alpha=.4, secondary_y=True)
    p_ax.set_xticklabels(p_df.strike.values, rotation=90, fontsize=9)
    p_ax.get_xaxis().set_minor_formatter(matplotlib.ticker.FormatStrFormatter('% 3.0f'))
    p_ax.set_ylim(0, 10)
    p_ax.right_ax.set_ylim(0, 12000)
    p_ax.set_title(p_date)
    p_ax.grid(True)
    _tlst = [x for x in p_df.strike.values if x < p_price]
    _uptlst = [x for x in p_df.strike.values if x > p_price]
    x_cordinate_annotate = len(_tlst)
    if ((len(p_df.strike.values) - len(_uptlst)) == len(_tlst)) and p_df.strike.values[x_cordinate_annotate] != p_price:
        _tmp = list()
        _tmp = [p_df.strike.values[x_cordinate_annotate], p_price, p_df.strike.values[x_cordinate_annotate - 1]]
        sorted_list = sorted(_tmp)
        normalized_sorted_list = (sorted_list - sorted_list[0])
        normalized_sorted_list = (normalized_sorted_list) / normalized_sorted_list[-1]
        x_cordinate_annotate = x_cordinate_annotate - 1 + normalized_sorted_list[1]
        # pdb.set_trace()

    # x_cordinate_annotate = len(_tlst)
    text_cordinate_annotate = x_cordinate_annotate / len(p_df.strike.values) - 0.01

    bbox_props = dict(boxstyle='round', fc='w', ec='k', lw=1)
    p_ax.annotate(f'{p_price:.2f}', (x_cordinate_annotate, 0), xytext=(text_cordinate_annotate, 0.78),
                  textcoords='axes fraction',
                  arrowprops=dict(arrowstyle="->",
                            connectionstyle="angle3"), bbox=bbox_props)
    # p_ax.annotate('Current Stock Price', xy=(600, 1000), xytext=(600, 2000),
    #               arrowprops={'facecolor': 'black', 'shrink': 0.005})

    return p_ax


def print_p_c_ratio_yf(p_ticker):
    tsla = yf.Ticker(p_ticker, session=session)
    price = tsla.get_info()['regularMarketPrice']
    price = tsla.history().tail(1)['Close'].values[0]
    load_dt = str(yf.download(tickers='TSLA', period='1d', interval='1d').reset_index()['Date'].values[0])[
              :10]  # YYYY-MM-DD format
    # tsla_oc = tsla.option_chain(p_date)
    df_p_c, weekly_fridays = [], []
    for i in range(0,3):
        weekly_friday = weekly_expiry[i].strftime('%Y-%m-%d')
        tsla_oc = tsla.option_chain(weekly_friday)
        weekly_fridays.append(weekly_friday)
        df_p_c.append(reshape_options_for_chart(tsla_oc, price, weekly_friday))

    # load_dt = tsla.option_chain(weekly_friday)[0].lastTradeDate.max().strftime('%Y-%m-%d')
    store_data(pd.concat(df_p_c), p_load_dt=load_dt)  # store into sqlite file

    fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(15, 6), constrained_layout=True, sharex=False, num="-")
    # fig.canvas.set_window_title('')
    ax0 = build_ax(df_p_c[0], ax0, weekly_fridays[0], price)
    ax1 = build_ax(df_p_c[1], ax1, weekly_fridays[1], price)
    ax2 = build_ax(df_p_c[2], ax2, weekly_fridays[2], price)
    plt.show()

    # print(tsla_pc)


def print_p_c_ratio_yf_bkup(p_ticker):
    tsla = yf.Ticker(p_ticker, session=session)
    price = tsla.get_info()['regularMarketPrice']
    # tsla_oc = tsla.option_chain(p_date)
    tsla_oc = tsla.option_chain(weekly_expiry[0].strftime('%Y-%m-%d'))
    tsla_pc = pd.concat([pd.DataFrame(tsla_oc.calls), pd.DataFrame(tsla_oc.puts)])

    del (tsla_oc)
    tsla_pc['put_call'] = tsla_pc['contractSymbol'].apply(lambda x: x[10])
    tsla_pc = tsla_pc.groupby(['strike', 'put_call'])['openInterest'].sum().unstack().dropna()
    tsla_pc = tsla_pc[~tsla_pc.isin([0., np.nan, np.inf, -np.inf]).any(1)]

    tsla_pc['total'] = tsla_pc.P + tsla_pc.C
    tsla_pc['p_c_ratio'] = tsla_pc.P / tsla_pc.C
    tsla_pc['c_p_ratio'] = tsla_pc.C / tsla_pc.P

    tsla_pc = tsla_pc.reset_index().sort_values(by=['strike'])
    nearest_strikes = (tsla_pc.strike < (price + 300)) & (tsla_pc.strike > (price - 200))
    tsla_pc = tsla_pc[nearest_strikes]

    tsla_pc.index = range(len(tsla_pc))
    df_p_c = tsla_pc.copy()

    fig, ax1 = plt.subplots(figsize=(25, 5))
    plt.title(p_date)
    fig.canvas.set_window_title('')

    df_p_c['p_c_ratio'].plot(kind='line', color='r', ax=ax1)
    df_p_c['c_p_ratio'].plot(kind='line', color='g', ax=ax1)
    df_p_c['P'].plot(kind='bar', color='r', alpha=.4, secondary_y=True)
    df_p_c['C'].plot(kind='bar', color='g', alpha=.4, secondary_y=True)
    ax1.set_xticklabels(df_p_c.strike.values, rotation=90)
    ax1.set_ylim(0, 10)
    ax1.right_ax.set_ylim(0, 15000)

    plt.show()

    print(tsla_pc)


def print_p_c_ratio(name):
    print_p_c_ratio_yf(name)
    return
    call_dict, put_dict, p_c_ratio_dict, c_p_ratio_dict, vol_dict = {}, {}, {}, {}, {}

    # Use a breakpoint in the code line below to debug your script.
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    # options.add_argument("--headless")
    options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(options=options)
    # driver.get('https://finance.yahoo.com/quote/' + ticker)
    # driver.find_element_by_xpath("//span[text()='Options']").click()

    driver.get('https://finance.yahoo.com/quote/TSLA/options?p=' + ticker + '&date=' + p_date)
    # driver.get(ticker)
    curr_price = driver.find_element_by_xpath(
        "//span[contains(@class,'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)')]").text
    curr_price = float(curr_price.replace(",", ""))

    elem = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//tr[contains(@class,'data-row')]")))
    # elem.click()

    date_select_box = Select(
        driver.find_element_by_xpath("//select[contains(@class,'Fz(s) H(25px) Bd Bdc($seperatorColor)')]"))
    chart_title = date_select_box.all_selected_options[0].text

    rows = driver.find_elements_by_xpath("//tr[contains(@class,'data-row')]")
    data = []
    data = [row.text for row in rows]
    pd.DataFrame.from_dict(data)
    df = pd.DataFrame.from_dict(data)
    df.columns = ['header']
    df = df.header.str.split(' ', expand=True)
    col_list = ['Contract Name', 'Last Trade Date', 'Last Trade Time', 'Last Trade TimeZone', 'Strike', 'Last Price',
                'Bid', 'Ask', 'Change', '% Change', 'Volume', 'Open Interest', 'Implied Vol']
    df.columns = col_list
    df['put_call'] = df['Contract Name'].apply(lambda x: x[10])

    df['Open Interest'] = df['Open Interest'].apply(lambda x: x.replace(",", ""))
    df['Open Interest'] = df['Open Interest'].apply(lambda x: x.replace("-", "0"))
    df['Open Interest'] = df['Open Interest'].apply(lambda x: re.findall('[-+]?\d*\.?\d+|\d+', x)[0])
    df_p_c = df.groupby(['Strike', 'put_call'])['Open Interest'].sum().unstack().dropna()
    df_p_c = df_p_c.reset_index().applymap(lambda x: float(x.replace(",", "")))
    df_p_c = df_p_c[~df_p_c.isin([0., np.nan, np.inf, -np.inf]).any(1)]

    df_p_c['total'] = df_p_c.P + df_p_c.C
    df_p_c['p_c_ratio'] = df_p_c.P / df_p_c.C
    df_p_c['c_p_ratio'] = df_p_c.C / df_p_c.P
    df_p_c = df_p_c.sort_values(by=['Strike'])
    df_p_c.index = range(len(df_p_c))

    fig, ax1 = plt.subplots(figsize=(25, 5))
    plt.title(chart_title)
    # plt.plot(df_p_c.Strike, df_p_c.p_c_ratio, color='r')
    # plt.plot(df_p_c.Strike, df_p_c.c_p_ratio, color='g')
    # plt.plot(df_p_c.Strike, df_p_c.P, color='r',secondary_y=True)
    # plt.plot(df_p_c.Strike, df_p_c.C, color='g',secondary_y=True)

    df_p_c['p_c_ratio'].plot(kind='line', color='r')
    df_p_c['c_p_ratio'].plot(kind='line', color='g')
    df_p_c['P'].plot(kind='bar', color='r', alpha=.4, secondary_y=True)
    df_p_c['C'].plot(kind='bar', color='g', alpha=.4, secondary_y=True)
    ax1.set_xticklabels(df_p_c.Strike.values, rotation=60)
    ax1.set_ylim(0, 10)
    plt.show()
    # print(df_p_c)

    # for row in rows:
    #     try:
    #         row_text = row.text
    #         print(row_text)
    #         op_type, strike, vol, open_interest = row_text[10], row_text.split()[4].replace(",", ""), row_text.split()[
    #             10].replace(",", ""), row_text.split()[11].replace(",", "")
    #         op_type, strike, vol, open_interest = op_type, float(strike), float(vol), float(open_interest)
    #
    #         if op_type == 'C':
    #             call_dict[strike] = open_interest
    #         else:
    #             put_dict[strike] = open_interest
    #
    #     except Exception:
    #         pass
    #
    # for strike in call_dict.keys():
    #     try:
    #         # put_call_ratio = put_dict[strike] / call_dict[strike]
    #         p_c_ratio_dict[strike] = float(put_dict[strike]) / float(call_dict[strike])
    #         c_p_ratio_dict[strike] = float(call_dict[strike]) / float(put_dict[strike])
    #         print(f'Strike: {strike} -> Put/Call = {p_c_ratio_dict[strike]}')
    #     except Exception:
    #         pass
    #
    #
    # put_list = [(s, p_c_ratio_dict[s]) for s in p_c_ratio_dict.keys() if abs(s - float(curr_price)) < width]
    # call_list = [(s, c_p_ratio_dict[s]) for s in c_p_ratio_dict.keys() if abs(s - float(curr_price)) < width]
    #
    # fig, ax1 = plt.subplots(figsize=(15, 5))
    # plt.title(chart_title)
    # plt.ylim(0, 3)
    # plt.plot(*zip(*put_list), color='red')
    # plt.plot(*zip(*call_list), color='green')
    # plt.plot()
    # plt.show()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_p_c_ratio(ticker)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

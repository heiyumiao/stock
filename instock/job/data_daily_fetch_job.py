#!/usr/local/bin/python3
# -*- coding: utf-8 -*-


import logging
import concurrent.futures
import pandas as pd
import os.path
import sys

cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
import instock.lib.run_template as runt
import instock.core.tablestructure as tbs
import instock.lib.database as mdb
import instock.core.indicator.calculate_indicator as idr
from instock.core.singleton_stock import stock_hist_data,stock_hist_min_data,etf_hist_min_data,etf_hist_data

__author__ = 'myh '
__date__ = '2023/3/10 '


def stock_hist_min(date):
    try:
        stocks_data = stock_hist_min_data(date=date).get_data()
        if stocks_data is None:
            return

    except Exception as e:
        logging.error(f"data_daily_fetch_job.stock_hist_min处理异常：{e}")

def etf_hist_min(date):
    try:
        stocks_data = etf_hist_min_data(date=date).get_data()
        if stocks_data is None:
            return

    except Exception as e:
        logging.error(f"data_daily_fetch_job.etf_hist_min处理异常：{e}")

def stock_hist(date):
    try:
        stocks_data = stock_hist_data(date=date).get_data()
        if stocks_data is None:
            return

    except Exception as e:
        logging.error(f"data_daily_fetch_job.stock_hist处理异常：{e}")
        
def etf_hist(date):
    try:
        stocks_data = etf_hist_data(date=date).get_data()
        if stocks_data is None:
            return

    except Exception as e:
        logging.error(f"data_daily_fetch_job.etf_hist处理异常：{e}")

def main():
    # 使用方法传递。
    runt.run_with_args(stock_hist_min)
    runt.run_with_args(etf_hist_min)
    runt.run_with_args(stock_hist)
    runt.run_with_args(etf_hist)


# main函数入口
if __name__ == '__main__':
    main()

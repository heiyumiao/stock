#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os.path
import datetime
import time
import numpy as np
import pandas as pd
import talib as tl
from retry import retry
import instock.core.tablestructure as tbs
import instock.lib.trade_time as trd
import instock.core.crawling.trade_date_hist as tdh
import instock.core.crawling.fund_etf_em as fee
import instock.core.crawling.stock_selection as sst
import instock.core.crawling.stock_lhb_em as sle
import instock.core.crawling.stock_lhb_sina as sls
import instock.core.crawling.stock_dzjy_em as sde
import instock.core.crawling.stock_hist_em as she
import instock.core.crawling.stock_fund_em as sff
import instock.core.crawling.stock_fhps_em as sfe
import traceback

__author__ = 'myh '
__date__ = '2023/3/10 '

# 设置基础目录，每次加载使用。
cpath_current = os.path.dirname(os.path.dirname(__file__))
stock_hist_cache_path = os.path.join(cpath_current, 'cache', 'hist_stock')
if not os.path.exists(stock_hist_cache_path):
    os.makedirs(stock_hist_cache_path)  # 创建多个文件夹结构。
etf_hist_cache_path = os.path.join(cpath_current, 'cache', 'hist_etf')
if not os.path.exists(etf_hist_cache_path):
    os.makedirs(etf_hist_cache_path)  # 创建多个文件夹结构。


# 600 601 603 605开头的股票是上证A股
# 600开头的股票是上证A股，属于大盘股，其中6006开头的股票是最早上市的股票，
# 6016开头的股票为大盘蓝筹股；900开头的股票是上证B股；
# 688开头的是上证科创板股票；
# 000开头的股票是深证A股，001、002开头的股票也都属于深证A股，
# 其中002开头的股票是深证A股中小企业股票；
# 200开头的股票是深证B股；
# 300、301开头的股票是创业板股票；400开头的股票是三板市场股票。
# 430、83、87开头的股票是北证A股
def is_a_stock(code):
    # 上证A股  # 深证A股
    return code.startswith(('600', '601', '603', '605', '000', '001', '002', '003', '300', '301'))


# 过滤掉 st 股票。
def is_not_st(name):
    return not name.startswith(('*ST', 'ST'))


# 过滤价格，如果没有基本上是退市了。
def is_open(price):
    return not np.isnan(price)


def is_open_with_line(price):
    return price != '-'


# 读取股票交易日历数据
def fetch_stocks_trade_date():
    try:
        data = tdh.tool_trade_date_hist_sina()
        if data is None or len(data.index) == 0:
            return None
        data_date = set(data['trade_date'].values.tolist())
        return data_date
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks_trade_date处理异常：{e}")
    return None


# 读取当天股票数据
def fetch_etfs(date):
    try:
        data = fee.fund_etf_spot_em()
        if data is None or len(data.index) == 0:
            return None
        if date is None:
            data.insert(0, 'date', datetime.datetime.now().strftime("%Y-%m-%d"))
        else:
            data.insert(0, 'date', date.strftime("%Y-%m-%d"))
        data.columns = list(tbs.TABLE_CN_ETF_SPOT['columns'])
        data = data.loc[data['new_price'].apply(is_open)]
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_etfs处理异常：{e}")
    return None


# 读取当天股票数据
def fetch_stocks(date):
    try:
        data = she.stock_zh_a_spot_em()
        if data is None or len(data.index) == 0:
            return None
        if date is None:
            data.insert(0, 'date', datetime.datetime.now().strftime("%Y-%m-%d"))
        else:
            data.insert(0, 'date', date.strftime("%Y-%m-%d"))
        data.columns = list(tbs.TABLE_CN_STOCK_SPOT['columns'])
        data = data.loc[data['code'].apply(is_a_stock)].loc[data['new_price'].apply(is_open)]
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks处理异常：{e}")
    return None


def fetch_stock_selection():
    try:
        data = sst.stock_selection()
        if data is None or len(data.index) == 0:
            return None
        data.columns = list(tbs.TABLE_CN_STOCK_SELECTION['columns'])
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks_selection处理异常：{e}")
    return None


# 读取股票资金流向
def fetch_stocks_fund_flow(index):
    try:
        cn_flow = tbs.CN_STOCK_FUND_FLOW[index]
        data = sff.stock_individual_fund_flow_rank(indicator=cn_flow['cn'])
        if data is None or len(data.index) == 0:
            return None
        data.columns = list(cn_flow['columns'])
        data = data.loc[data['code'].apply(is_a_stock)].loc[data['new_price'].apply(is_open_with_line)]
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks_fund_flow处理异常：{e}")
    return None


# 读取板块资金流向
def fetch_stocks_sector_fund_flow(index_sector, index_indicator):
    try:
        cn_flow = tbs.CN_STOCK_SECTOR_FUND_FLOW[1][index_indicator]
        data = sff.stock_sector_fund_flow_rank(indicator=cn_flow['cn'], sector_type=tbs.CN_STOCK_SECTOR_FUND_FLOW[0][index_sector])
        if data is None or len(data.index) == 0:
            return None
        data.columns = list(cn_flow['columns'])
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks_sector_fund_flow处理异常：{e}")
    return None


# 读取股票分红配送
def fetch_stocks_bonus(date):
    try:
        data = sfe.stock_fhps_em(date=trd.get_bonus_report_date())
        if data is None or len(data.index) == 0:
            return None
        if date is None:
            data.insert(0, 'date', datetime.datetime.now().strftime("%Y-%m-%d"))
        else:
            data.insert(0, 'date', date.strftime("%Y-%m-%d"))
        data.columns = list(tbs.TABLE_CN_STOCK_BONUS['columns'])
        data = data.loc[data['code'].apply(is_a_stock)]
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stocks_bonus处理异常：{e}")
    return None


# 股票近三月上龙虎榜且必须有2次以上机构参与的
def fetch_stock_top_entity_data(date):
    run_date = date + datetime.timedelta(days=-90)
    start_date = run_date.strftime("%Y%m%d")
    end_date = date.strftime("%Y%m%d")
    code_name = '代码'
    entity_amount_name = '买方机构数'
    try:
        data = sle.stock_lhb_jgmmtj_em(start_date, end_date)
        if data is None or len(data.index) == 0:
            return None

        # 机构买入次数大于1计算方法，首先：每次要有买方机构数(>0),然后：这段时间买方机构数求和大于1
        mask = (data[entity_amount_name] > 0)  # 首先：每次要有买方机构数(>0)
        data = data.loc[mask]

        if len(data.index) == 0:
            return None

        grouped = data.groupby(by=data[code_name])
        data_series = grouped[entity_amount_name].sum()
        data_code = set(data_series[data_series > 1].index.values)  # 然后：这段时间买方机构数求和大于1

        if not data_code:
            return None

        return data_code
    except Exception as e:
        logging.error(f"stockfetch.fetch_stock_top_entity_data处理异常：{e}")
    return None


# 描述: 获取新浪财经-龙虎榜-个股上榜统计
def fetch_stock_top_data(date):
    try:
        data = sls.stock_lhb_ggtj_sina(recent_day="5")
        if data is None or len(data.index) == 0:
            return None
        _columns = list(tbs.TABLE_CN_STOCK_TOP['columns'])
        _columns.pop(0)
        data.columns = _columns
        data = data.loc[data['code'].apply(is_a_stock)]
        data.drop_duplicates('code', keep='last', inplace=True)
        if date is None:
            data.insert(0, 'date', datetime.datetime.now().strftime("%Y-%m-%d"))
        else:
            data.insert(0, 'date', date.strftime("%Y-%m-%d"))
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stock_top_data处理异常：{e}")
    return None


# 描述: 获取东方财富网-数据中心-大宗交易-每日统计
def fetch_stock_blocktrade_data(date):
    date_str = date.strftime("%Y%m%d")
    try:
        data = sde.stock_dzjy_mrtj(start_date=date_str, end_date=date_str)
        if data is None or len(data.index) == 0:
            return None

        columns = list(tbs.TABLE_CN_STOCK_BLOCKTRADE['columns'])
        columns.insert(0, 'index')
        data.columns = columns
        data = data.loc[data['code'].apply(is_a_stock)]
        data.drop('index', axis=1, inplace=True)
        return data
    except TypeError:
        logging.error("处理异常：目前还没有大宗交易数据，请17:00点后再获取！")
        return None
    except Exception as e:
        logging.error(f"stockfetch.fetch_stock_blocktrade_data处理异常：{e}")
    return None


# 读取etf历史数据   
@retry(tries=3, delay=2) #自动重试机制会处理失败情况
def fetch_etf_hist(data_base, date_start=None, date_end=None,is_cache=True, adjust='qfq'):
    date = data_base[0]
    code = data_base[1]

    if date_start is None:
        date_start, is_cache = trd.get_trade_hist_interval(date)  # 提高运行效率，只运行一次
    try:
        cache_dir = os.path.join(etf_hist_cache_path, "daily")
        # 全部存在一个一个文件里面
        try:
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
        except Exception:
            pass
        cache_file = os.path.join(cache_dir, "%s%s.gzip.pickle" % (code, adjust))
        # 如果缓存存在就直接返回缓存数据。压缩方式。
        if os.path.isfile(cache_file):
            cached_data = pd.read_pickle(cache_file, compression="gzip")

            # 获取今天的数据(目前只获取一天，添加到缓存中，todo：获取多天数据，合并进去，防止前面有意外没成功的)
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            latest_stock = fee.fund_etf_hist_em(symbol=code, period="daily", start_date=today_str, adjust=adjust)

            if latest_stock is not None and len(latest_stock.index) > 0:
                latest_stock.columns = tuple(tbs.CN_STOCK_HIST_DATA['columns'])

                # 合并缓存数据与最新数据
                stock = pd.concat([cached_data, latest_stock], ignore_index=True)

                if is_cache:
                    stock.to_pickle(cache_file, compression="gzip")
        else:
            if date_end is not None:
                stock = fee.fund_etf_hist_em(symbol=code, period="daily", start_date=date_start, end_date=date_end,
                                            adjust=adjust)
            else:
                stock = fee.fund_etf_hist_em(symbol=code, period="daily", start_date=date_start, adjust=adjust)

            if stock is None or len(stock.index) == 0:
                return None
            stock.columns = tuple(tbs.CN_STOCK_HIST_DATA['columns'])
            stock = stock.sort_index()  # 将数据按照日期排序下。
            try:
                if is_cache:
                    stock.to_pickle(cache_file, compression="gzip")
            except Exception as e:
                pass
            # time.sleep(0.3)
        data=stock
        if data is not None:
            data.loc[:, 'p_change'] = tl.ROC(data['close'].values, 1)
            data['p_change'].values[np.isnan(data['p_change'].values)] = 0.0
            data["volume"] = data['volume'].values.astype('double') * 100  # 成交量单位从手变成股。
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_etf_hist处理异常：{e}")
        raise
    return None


# 读取股票历史数据
def fetch_stock_hist(data_base, date_start=None, is_cache=True):
    date = data_base[0]
    code = data_base[1]

    if date_start is None:
        date_start, is_cache = trd.get_trade_hist_interval(date)  # 提高运行效率，只运行一次
        # date_end = date_end.strftime("%Y%m%d")
    try:
        data = stock_hist_cache(code, date_start, None, is_cache, 'qfq')
        if data is not None:
            data.loc[:, 'p_change'] = tl.ROC(data['close'].values, 1)
            data['p_change'].values[np.isnan(data['p_change'].values)] = 0.0
            data["volume"] = data['volume'].values.astype('double') * 100  # 成交量单位从手变成股。
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stock_hist处理异常：{e}")
    return None


# 增加读取股票缓存方法。加快处理速度。多线程解决效率
@retry(tries=3, delay=2) #自动重试机制会处理失败情况
def stock_hist_cache(code, date_start, date_end=None, is_cache=True, adjust=''):
    cache_dir = os.path.join(stock_hist_cache_path, "daily")
    # 全部存在一个一个文件里面
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    except Exception:
        pass
    cache_file = os.path.join(cache_dir, "%s%s.gzip.pickle" % (code, adjust))
    # 如果缓存存在就直接返回缓存数据。压缩方式。
    try:
        if os.path.isfile(cache_file):
            cached_data = pd.read_pickle(cache_file, compression="gzip")

            # 获取今天的数据(目前只获取一天，添加到缓存中，todo：获取多天数据，合并进去，防止前面有意外没成功的)
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            latest_stock = she.stock_zh_a_hist(symbol=code, period="daily", start_date=today_str, adjust=adjust)

            if latest_stock is not None and len(latest_stock.index) > 0:
                latest_stock.columns = tuple(tbs.CN_STOCK_HIST_DATA['columns'])

                # 合并缓存数据与最新数据
                stock = pd.concat([cached_data, latest_stock], ignore_index=True)

                if is_cache:
                    stock.to_pickle(cache_file, compression="gzip")
                
                return stock
        else:
            if date_end is not None:
                stock = she.stock_zh_a_hist(symbol=code, period="daily", start_date=date_start, end_date=date_end,
                                            adjust=adjust)
            else:
                stock = she.stock_zh_a_hist(symbol=code, period="daily", start_date=date_start, adjust=adjust)

            if stock is None or len(stock.index) == 0:
                return None
            stock.columns = tuple(tbs.CN_STOCK_HIST_DATA['columns'])
            stock = stock.sort_index()  # 将数据按照日期排序下。
            try:
                if is_cache:
                    stock.to_pickle(cache_file, compression="gzip")
            except Exception as e:
                pass
            time.sleep(0.3)
            return stock
    except Exception as e:
        logging.error(f"stockfetch.stock_hist_cache处理异常：{code}代码{e}")
        raise
    return None








# 读取股票历史数据# min
@retry(tries=3, delay=2) #自动重试机制会处理失败情况
def fetch_stock_hist_min(data_base, date_start=None, is_cache=True):
    date = data_base[0]
    code = data_base[1]

    try:
        data = stock_hist_min_cache(code, date_start, None, is_cache, 'qfq')
        if data is not None:
            data.loc[:, 'p_change'] = tl.ROC(data['close'].values, 1)
            data['p_change'].values[np.isnan(data['p_change'].values)] = 0.0
            data["volume"] = data['volume'].values.astype('double') * 100  # 成交量单位从手变成股。
        time.sleep(0.3)
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_stock_hist_min处理异常：{e}")
        raise
    return None

def stock_hist_min_cache(code, date_start, date_end=None, is_cache=True, adjust=''):
    cache_dir = os.path.join(stock_hist_cache_path, "min",date_start[0:6])
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    except Exception:
        pass
    cache_file = os.path.join(cache_dir, "%s%s.gzip.pickle" % (code, adjust))
    # 如果缓存存在就直接返回缓存数据。压缩方式。
    try:
        if os.path.isfile(cache_file):
            existing_data = pd.read_pickle(cache_file, compression="gzip")
        else:
            existing_data = pd.DataFrame()
        
        new_stock_data = she.stock_zh_a_hist_min_em(symbol=code, period="1",  adjust=adjust)

        # If no new data or data is empty, return the existing data
        if new_stock_data is None or new_stock_data.empty:
            return existing_data if not existing_data.empty else None

        # Set the correct column names
        new_stock_data.columns = tuple(tbs.CN_STOCK_HIST_MIN_DATA['columns'])
        new_stock_data = new_stock_data.sort_index()
        
        # Append new data to the existing data, avoiding duplicates based on 'date' 
        # 但不会刷新原有数据
        if not existing_data.empty:
            existing_data['date'] = pd.to_datetime(existing_data['date'])
            new_stock_data['date'] = pd.to_datetime(new_stock_data['date'])
            
            # Filter out rows from new_etf_data that already exist in existing_data
            new_stock_data = new_stock_data[~new_stock_data['date'].isin(existing_data['date'])]

        combined_data = pd.concat([existing_data, new_stock_data], ignore_index=True)
        # Sort the combined data by date,but not reset index
        # combined_data = combined_data.sort_values(by='date').reset_index(drop=True)
        combined_data = combined_data.sort_values(by='date')
        # Save the combined data back to the cache file
        combined_data.to_pickle(cache_file, compression="gzip")

        # Return the combined data
        return combined_data
    
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f"stockfetch.etf_hist_min_cache处理异常：{code}代码{e}\n")
        raise
    return None

# 读取etf历史数据  min
@retry(tries=3, delay=2) #自动重试机制会处理失败情况
def fetch_etf_hist_min(data_base, date_start=None, adjust='qfq'):
    date = data_base[0]
    code = data_base[1]

    try:
        data = etf_hist_min_cache(code, date_start, None, 'qfq')
        
        if data is None or len(data.index) == 0:
            return None
        data.columns = tuple(tbs.CN_STOCK_HIST_MIN_DATA['columns'])
        data = data.sort_index()  # 将数据按照日期排序下。
        if data is not None:
            data.loc[:, 'p_change'] = tl.ROC(data['close'].values, 1)
            data['p_change'].values[np.isnan(data['p_change'].values)] = 0.0
            data["volume"] = data['volume'].values.astype('double') * 100  # 成交量单位从手变成股。
        return data
    except Exception as e:
        logging.error(f"stockfetch.fetch_etf_hist_min处理异常：{e}")
        raise
    return None


def etf_hist_min_cache(code, date_start, date_end=None, adjust=''):
    cache_dir = os.path.join(etf_hist_cache_path,"min", date_start[0:6])
    try:
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    except Exception:
        pass
    cache_file = os.path.join(cache_dir, "%s%s.gzip.pickle" % (code, adjust))
    # 如果缓存存在就直接返回缓存数据。压缩方式。
    try:
        if os.path.isfile(cache_file):
            existing_data = pd.read_pickle(cache_file, compression="gzip")
        else:
            existing_data = pd.DataFrame()
        
        new_etf_data = fee.fund_etf_hist_min_em(symbol=code, period="1",  adjust=adjust)

        # If no new data or data is empty, return the existing data
        if new_etf_data is None or new_etf_data.empty:
            return existing_data if not existing_data.empty else None

        # Set the correct column names
        new_etf_data.columns = tuple(tbs.CN_STOCK_HIST_MIN_DATA['columns'])  #复用
        new_etf_data = new_etf_data.sort_index()

        # Append new data to the existing data, avoiding duplicates based on 'date' 
        # 但不会刷新原有数据
        if not existing_data.empty:
            existing_data['date'] = pd.to_datetime(existing_data['date'])
            new_etf_data['date'] = pd.to_datetime(new_etf_data['date'])
            
            # Filter out rows from new_etf_data that already exist in existing_data
            new_etf_data = new_etf_data[~new_etf_data['date'].isin(existing_data['date'])]

        combined_data = pd.concat([existing_data, new_etf_data], ignore_index=True)
        # Sort the combined data by date,but not reset index
        # combined_data = combined_data.sort_values(by='date').reset_index(drop=True)
        combined_data = combined_data.sort_values(by='date')
        # Save the combined data back to the cache file
        combined_data.to_pickle(cache_file, compression="gzip")

        # Return the combined data
        return combined_data
    
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f"stockfetch.etf_hist_min_cache处理异常：{code}代码{e}\n")
        raise
    return None

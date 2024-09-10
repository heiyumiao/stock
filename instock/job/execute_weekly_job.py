#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#用来保存分钟数据

import time
import datetime
import concurrent.futures
import logging
import os.path
import sys

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
log_path = os.path.join(cpath_current, 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path)
logging.basicConfig(format='%(asctime)s %(message)s', filename=os.path.join(log_path, 'stock_weekly_job.log'))
logging.getLogger().setLevel(logging.INFO)
import init_job as bj
import basic_data_daily_job as hdj
import basic_data_other_daily_job as hdtj
import basic_data_after_close_daily_job as acdj
import indicators_data_daily_job as gdj
import strategy_data_daily_job as sdj
import backtest_data_daily_job as bdj
import klinepattern_data_daily_job as kdj
import selection_data_daily_job as sddj
import data_daily_fetch_job as ewj

__author__ = 'qyf '
__date__ = '2024年8月23日'


def main():
    start = time.time()
    _start = datetime.datetime.now()
    logging.info("######## 周任务执行时间: %s #######" % _start.strftime("%Y-%m-%d %H:%M:%S.%f"))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        #
        executor.submit(ewj.main)


    logging.info("######## 完成任务, 使用时间: %s 秒 #######" % (time.time() - start))


# main函数入口
if __name__ == '__main__':
    main()

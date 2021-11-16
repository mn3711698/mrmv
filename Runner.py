# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import talib
import logging
from apscheduler.schedulers.background import BlockingScheduler

import config
from RunUse.AbstractTradeRun import AbstractTradeRun
from config import get_symbol_metas, timezone
import sys


formats = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=formats, filename='gmlog_print.txt')
logger = logging.getLogger('print')
logging.getLogger("apscheduler").setLevel(logging.WARNING)  # 设置apscheduler.


if __name__ == '__main__':  # 25
    group_name = None
    if len(sys.argv) >= 2:
        group_name = sys.argv[1]
    RunTrade = AbstractTradeRun(config.config_raw, group_name)
    scheduler = BlockingScheduler(timezone=timezone)  # 定时的任务.

    scheduler.add_job(RunTrade.get_line_1min, trigger='cron', id='TradeRunS1_1', second='2')  # 1min
    #####################################################################################

    scheduler.add_job(RunTrade.get_position, trigger='cron', id='TradeRunGMRMp', second='*/10')
    scheduler.start()

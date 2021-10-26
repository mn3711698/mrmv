# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import talib
import logging
from apscheduler.schedulers.background import BlockingScheduler
from RunUse.AbstractTradeRun import AbstractTradeRun
from config import get_symbol_metas, timezone
import sys


formats = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=formats, filename='gmlog_print.txt')
logger = logging.getLogger('print')
logging.getLogger("apscheduler").setLevel(logging.WARNING)  # 设置apscheduler.


if __name__ == '__main__':  # 25
    if len(sys.argv) < 2:
        symbol_metas = get_symbol_metas()
    else:
        symbol_metas = get_symbol_metas(sys.argv[1])
    RunTrade = AbstractTradeRun(get_symbol_metas())
    scheduler = BlockingScheduler(timezone=timezone)  # 定时的任务.

    scheduler.add_job(RunTrade.get_line_1min, trigger='cron', id='TradeRunS1_1', second='2')  # 1min
    #####################################################################################

    scheduler.add_job(RunTrade.get_position, trigger='cron', id='TradeRunGMRMp', second='*/10')
    scheduler.start()

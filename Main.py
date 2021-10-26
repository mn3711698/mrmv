# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import talib
import logging
from apscheduler.schedulers.background import BlockingScheduler
from RunUse.TradeRunMain import TradeRunMain
from config import get_symbol_metas

formats = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=formats, filename='gmlog_print.txt')
logger = logging.getLogger('print')
logging.getLogger("apscheduler").setLevel(logging.WARNING)  # 设置apscheduler.


if __name__ == '__main__':  # 25
    RunTrade = TradeRunMain(get_symbol_metas('@select_symbols_1'))
    scheduler = BlockingScheduler()  # 定时的任务.
    # minute_3 = '0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57'
    # minute_5 = '0,5,10,15,20,25,30,35,40,45,50,55'
    # minute_15 = '0,15,30,45'
    # minute_30 = '0,30'
    # hour_2 = '0,2,4,6,8,10,12,14,16,18,20,22'
    # hour_4 = '0,4,8,12,16,20'

    scheduler.add_job(RunTrade.get_line_1min, trigger='cron', id='TradeRunS1_1', second='2')  # 1min
    ###########################################################################################
    scheduler.add_job(RunTrade.get_position, trigger='cron', id='TradeRunSp', second='*/10')
    scheduler.start()

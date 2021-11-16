# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import logging

import config
from RunUse.AbstractTradeRun import AbstractTradeRun
import sys


formats = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=formats, filename='gmlog_print.txt')
logger = logging.getLogger('print')
logging.getLogger("apscheduler").setLevel(logging.WARNING)  # 设置apscheduler.


if __name__ == '__main__':  # 25
    group_name = None
    if len(sys.argv) >= 2:
        group_name = sys.argv[1]
    trader = AbstractTradeRun(config.config_raw, group_name)
    trader.start()

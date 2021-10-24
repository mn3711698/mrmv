# -*- coding: utf-8 -*-
##############################################################################
# Author：QQ173782910
##############################################################################

import time
import traceback
from utils.brokers import Broker
from getaway.binance_http import BinanceFutureHttp
from getaway.send_msg import bugcode, getToday, dingding
from constant.constant import (EVENT_POS, EVENT_KLINE)
from utils.event import EventEngine, Event
from strategies.LineWith import LineWith
from config import key, secret, redisc


class TradeRunMain:

    def __init__(self, symbols_conf):
        self.min_volume_dict = {}
        self.symbols_list = []
        self.symbols_dict = {}
        self.trading_size_dict = {}
        self.kline_time_dict = {}
        self.redisc = redisc
        self.conf_initialize(symbols_conf)
        self.bugcode = bugcode
        self.getToday = getToday
        self.dingding = dingding
        self.min_volume = 0.001
        self.time_stop = 0.4
        self.key = key
        self.secret = secret
        self.engine = EventEngine()
        self.broker = Broker(self.engine, self.key, secret=self.secret, symbols_list=self.symbols_list)
        self.initialization_data()
        self.broker.add_strategy(LineWith, self.symbols_dict, self.min_volume_dict, self.trading_size_dict)

    def conf_initialize(self, symbolsconf):
        # 初始化dict
        # [symbol, trading_size, win_arg, add_arg]
        for i in symbolsconf:
            symbol, trading_size, win_arg, add_arg = i
            self.symbols_list.append(symbol)
            self.symbols_dict[symbol] = [win_arg, add_arg]
            self.trading_size_dict[symbol] = trading_size

    def initialization_data(self):
        try:
            binance_http = BinanceFutureHttp(key=self.key, secret=self.secret)
            einfo = binance_http.exchangeInfo()
            if isinstance(einfo, dict):
                esymbols = einfo['symbols']
                for i in esymbols:
                    _symbol = i['symbol']
                    if _symbol in self.trading_size_dict:
                        for j in i['filters']:
                            if j['filterType'] == 'LOT_SIZE':
                                minQty = float(j['minQty'])
                                trading_size = self.trading_size_dict[_symbol]
                                if minQty > trading_size:
                                    self.trading_size_dict[_symbol] = minQty
                                    msg = f"config里的symbol:{_symbol},trading_size:{trading_size},太小,minQty{minQty}"
                                    self.bugcode(msg)
                                self.min_volume_dict[_symbol] = minQty
        except:
            self.bugcode(traceback, "mrmv_TradeRun_initialization_data")

    def get_line_1min(self):
        minute_3 = ['00', '03', '06', '09', '12', '15', '18', '21', '24', '27', '30', '33', '36', '39', '42', '45',
                    '48', '51', '54', '57']
        minute_5 = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55']
        minute_15 = ['00', '15', '30', '45']
        minute_30 = ['00', '30']
        hour_2 = ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22']
        hour_4 = ['00', '04', '08', '12', '16', '20']
        symbol_list = [
            ["LRCUSDT", 25, 501], ["HBARUSDT", 26, -50], ["CHRUSDT", 27, 86], ["SKLUSDT", 24, 90],
            ["NKNUSDT", 25, 94], ["XLMUSDT", 26, -10], ["BZRXUSDT", 26, 15], ["CHZUSDT", 27, 100],
            ["1000XECUSDT", 27, -15], ["BLZUSDT", 23, 35], ["DOGEUSDT", 22, 700], ["TLMUSDT", 25, 100],
            ["ONEUSDT", 27, -4], ["XEMUSDT", 27, 35], ["CELRUSDT", 30, -33], ["VETUSDT", 29, 30],
            ["RVNUSDT", 27, 5], ["GALAUSDT", 26, 20], ["ZILUSDT", 23, -25], ["TRXUSDT", 21, -20],
            ["ANKRUSDT", 21, -2], ["IOSTUSDT", 23, 80], ["DGBUSDT", 23, -30], ["RSRUSDT", 23, -30],
            ["LINAUSDT", 26, 60], ["BTSUSDT", 26, 60], ["STMXUSDT", 22, 25], ["AKROUSDT", 24, 110],
            ["SCUSDT", 22, 300], ["1000SHIBUSDT", 24, 300], ["DENTUSDT", 28, -30]
        ]
        bought = 75
        sold_bar = 10
        bought_bar = 10
        interval = '1m'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_1min:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)
        ti = self.getToday(2)
        h, m = ti.split(':')
        # print(h, m, 'ttttttttttttttttt')
        # 判断分钟 3,5,15,30
        if m in minute_3:
            self.get_line_3min()
        if m in minute_5:
            self.get_line_5min()
        if m in minute_15:
            self.get_line_15min()
        if m in minute_30:
            self.get_line_30min()

        self.get_line_1h()

        # 判断时钟 1h,2h,4h
        if h in hour_2:
            self.get_line_2h()
        if h in hour_4:
            self.get_line_4h()

    def get_line_3min(self):

        symbol_list = [
            ["LRCUSDT", 26, -7], ["HBARUSDT", 28, 60], ["CHRUSDT", 26, 25], ["SKLUSDT", 26, 100],
            ["NKNUSDT", 24, 78], ["XLMUSDT", 26, 70], ["BZRXUSDT", 27, 150], ["CHZUSDT", 28, 100],
            ["1000XECUSDT", 27, -15], ["BLZUSDT", 26, 150], ["DOGEUSDT", 22, -15], ["TLMUSDT", 30, -23],
            ["ONEUSDT", 25, 33], ["XEMUSDT", 30, 50], ["CELRUSDT", 30, 46], ["VETUSDT", 30, 150],
            ["RVNUSDT", 27, 100], ["GALAUSDT", 26, 80], ["ZILUSDT", 26, 80], ["TRXUSDT", 25, 100],
            ["ANKRUSDT", 25, 50], ["IOSTUSDT", 27, 15], ["DGBUSDT", 23, 60], ["RSRUSDT", 24, -30],
            ["LINAUSDT", 27, 50], ["BTSUSDT", 27, 50], ["STMXUSDT", 24, -20], ["AKROUSDT", 26, 35],
            ["SCUSDT", 23, 100], ["1000SHIBUSDT", 28, -50], ["DENTUSDT", 29, 25]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '3m'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_3min:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_5min(self):

        symbol_list = [
            ["LRCUSDT", 26, 93], ["HBARUSDT", 28, 23], ["CHRUSDT", 27, 25], ["SKLUSDT", 26, 35],
            ["NKNUSDT", 27, 83], ["XLMUSDT", 30, 41], ["BZRXUSDT", 30, 44], ["CHZUSDT", 27, 35],
            ["1000XECUSDT", 27, 100], ["BLZUSDT", 30, 90], ["DOGEUSDT", 26, 55], ["TLMUSDT", 30, 85],
            ["ONEUSDT", 29, -17], ["XEMUSDT", 30, -35], ["CELRUSDT", 28, 100], ["VETUSDT", 29, -22],
            ["RVNUSDT", 28, 41], ["GALAUSDT", 27, 25], ["ZILUSDT", 30, 11], ["TRXUSDT", 26, -45],
            ["ANKRUSDT", 28, 50], ["IOSTUSDT", 28, 80], ["DGBUSDT", 25, 27], ["RSRUSDT", 26, 70],
            ["LINAUSDT", 27, 60], ["BTSUSDT", 27, -22], ["STMXUSDT", 26, 80], ["AKROUSDT", 27, 17],
            ["SCUSDT", 25, -19], ["1000SHIBUSDT", 28, -20], ["DENTUSDT", 31, -20]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '5m'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_5min:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_15min(self):

        symbol_list = [
            ["LRCUSDT", 26, -16], ["HBARUSDT", 29, 25], ["CHRUSDT", 27, 85], ["SKLUSDT", 26, 20],
            ["NKNUSDT", 27, 100], ["XLMUSDT", 29, 47], ["BZRXUSDT", 30, 100], ["CHZUSDT", 30, -30],
            ["1000XECUSDT", 28, -33], ["BLZUSDT", 30, 20], ["DOGEUSDT", 26, 100], ["TLMUSDT", 32, 100],
            ["ONEUSDT", 33, 58], ["XEMUSDT", 31, -6], ["CELRUSDT", 30, 30], ["VETUSDT", 30, -6],
            ["RVNUSDT", 29, -13], ["GALAUSDT", 28, -5], ["ZILUSDT", 30, 110], ["TRXUSDT", 27, 50],
            ["ANKRUSDT", 30, 80], ["IOSTUSDT", 29, 20], ["DGBUSDT", 30, 50], ["RSRUSDT", 26, 60],
            ["LINAUSDT", 30, 60], ["BTSUSDT", 28, 100], ["STMXUSDT", 27, 10], ["AKROUSDT", 28, 90],
            ["SCUSDT", 28, -20], ["1000SHIBUSDT", 28, 35], ["DENTUSDT", 31, 90]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '15m'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_15min:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_30min(self):

        symbol_list = [
            ["LRCUSDT", 28, 20], ["HBARUSDT", 34, 51], ["CHRUSDT", 29, 69], ["SKLUSDT", 27, 27],
            ["NKNUSDT", 28, 35], ["XLMUSDT", 32, 31], ["BZRXUSDT", 30, 65], ["CHZUSDT", 33, 50],
            ["1000XECUSDT", 29, 100], ["BLZUSDT", 31, 55], ["DOGEUSDT", 28, 30], ["TLMUSDT", 32, 32],
            ["ONEUSDT", 33, 65], ["XEMUSDT", 33, 24], ["CELRUSDT", 31, 52], ["VETUSDT", 30, 32],
            ["RVNUSDT", 30, 25], ["GALAUSDT", 28, 80], ["ZILUSDT", 32, 25], ["TRXUSDT", 29, -3],
            ["ANKRUSDT", 31, 24], ["IOSTUSDT", 30, 36], ["DGBUSDT", 32, -22], ["RSRUSDT", 28, 35],
            ["LINAUSDT", 32, 70], ["BTSUSDT", 29, 140], ["STMXUSDT", 33, 30], ["AKROUSDT", 30, 55],
            ["SCUSDT", 29, 40], ["1000SHIBUSDT", 28, 70], ["DENTUSDT", 31, 50]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '30m'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_30min:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_1h(self):

        symbol_list = [
            ["LRCUSDT", 30, 29], ["HBARUSDT", 35, 30], ["CHRUSDT", 32, 47], ["SKLUSDT", 30, 19],
            ["NKNUSDT", 29, 11], ["XLMUSDT", 32, 43], ["BZRXUSDT", 32, 24], ["CHZUSDT", 34, 20],
            ["1000XECUSDT", 32, -23], ["BLZUSDT", 31, -20], ["DOGEUSDT", 28, 30], ["TLMUSDT", 34, 22],
            ["ONEUSDT", 33, 23], ["XEMUSDT", 31, -15], ["CELRUSDT", 31, 21], ["VETUSDT", 32, 55],
            ["RVNUSDT", 31, 21], ["GALAUSDT", 32, 35], ["ZILUSDT", 32, 31], ["TRXUSDT", 31, 14],
            ["ANKRUSDT", 32, 33], ["IOSTUSDT", 30, 35], ["DGBUSDT", 35, 45], ["RSRUSDT", 30, 13],
            ["LINAUSDT", 33, 36], ["BTSUSDT", 30, 45], ["STMXUSDT", 34, 29], ["AKROUSDT", 30, 180],
            ["SCUSDT", 30, 35], ["1000SHIBUSDT", 29, 25], ["DENTUSDT", 32, 10]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '1h'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_1h:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_2h(self):

        symbol_list = [
            ["LRCUSDT", 30, 77], ["HBARUSDT", 34, -19], ["CHRUSDT", 33, 50], ["SKLUSDT", 31, 48],
            ["NKNUSDT", 30, 65], ["XLMUSDT", 32, 26], ["BZRXUSDT", 35, 15], ["CHZUSDT", 34, 100],
            ["1000XECUSDT", 34, -45], ["BLZUSDT", 32, 55], ["DOGEUSDT", 29, 60], ["TLMUSDT", 30, 100],
            ["ONEUSDT", 33, 42], ["XEMUSDT", 30, 31], ["CELRUSDT", 31, -13], ["VETUSDT", 32, 22],
            ["RVNUSDT", 31, 26], ["GALAUSDT", 33, 50], ["ZILUSDT", 34, 30], ["TRXUSDT", 32, 90],
            ["ANKRUSDT", 32, 100], ["IOSTUSDT", 31, 20], ["DGBUSDT", 35, 35], ["RSRUSDT", 33, 31],
            ["LINAUSDT", 34, 60], ["BTSUSDT", 33, 70], ["STMXUSDT", 34, 60], ["AKROUSDT", 32, 60],
            ["SCUSDT", 30, 36], ["1000SHIBUSDT", 33, 30], ["DENTUSDT", 32, 15]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '2h'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_2h:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_line_4h(self):

        symbol_list = [
            ["LRCUSDT", 33, 28], ["HBARUSDT", 35, 25], ["CHRUSDT", 35, 28], ["SKLUSDT", 34, 45],
            ["NKNUSDT", 34, -11], ["XLMUSDT", 32, 55], ["BZRXUSDT", 34, 31], ["CHZUSDT", 34, 22],
            ["1000XECUSDT", 32, 45], ["BLZUSDT", 34, 31], ["DOGEUSDT", 34, 34], ["TLMUSDT", 33, 100],
            ["ONEUSDT", 33, 85], ["XEMUSDT", 33, 47], ["CELRUSDT", 33, 47], ["VETUSDT", 35, -3],
            ["RVNUSDT", 32, 30], ["GALAUSDT", 35, -30], ["ZILUSDT", 35, -2], ["TRXUSDT", 34, 35],
            ["ANKRUSDT", 33, 36], ["IOSTUSDT", 33, 25], ["DGBUSDT", 35, 50], ["RSRUSDT", 35, 30],
            ["LINAUSDT", 34, -5], ["BTSUSDT", 33, 25], ["STMXUSDT", 34, 27], ["AKROUSDT", 35, 21],
            ["SCUSDT", 30, 60], ["1000SHIBUSDT", 33, 25], ["DENTUSDT", 35, 53]
        ]
        bought = 70
        sold_bar = 10
        bought_bar = 10
        interval = '4h'
        for i in symbol_list:
            symbol, sold, contrast = i
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_4h:{symbol},{interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, interval, contrast)
            time.sleep(self.time_stop)

    def get_kline_data(self, symbol, sold, bought, sold_bar, bought_bar, interval, contrast):
        try:

            if symbol in self.symbols_dict:
                try:
                    data = self.broker.binance_http.get_kline_interval(symbol=symbol, interval=interval, limit=100)
                except Exception as e:
                    # self.bugcode(f"{symbol},{interval},get_kline_data:{e}")
                    # print(e)
                    data = self.broker.binance_http.get_kline_interval(symbol=symbol, interval=interval, limit=100)
                if isinstance(data, list):
                    if len(data):
                        kline_time = data[-1][0]
                        if kline_time != self.kline_time_dict.get(symbol+interval, 0):
                            edata = {'symbol': symbol, "data": data, "sold": sold, "bought": bought,
                                     "sold_bar": sold_bar, "bought_bar": bought_bar, 'interval': interval,
                                     "contrast": contrast}
                            event = Event(EVENT_KLINE, edata)
                            self.broker.event_engine.put(event)
                            self.kline_time_dict[symbol+interval] = kline_time
                    return True
                else:
                    self.dingding(f"注意是不是超并发了或者时间不对，{data}", symbol)
                    self.bugcode(f"{symbol},{interval},{data}")
                    return False
        except:
            self.bugcode(traceback, "mrmv_TradeRun_get_kline_data")
        return False

    def get_position(self):
        try:
            try:
                info = self.broker.binance_http.get_position_info()
            except Exception as e:
                # self.bugcode(f"get_position:{e}")
                info = self.broker.binance_http.get_position_info()
            if isinstance(info, list):
                for item in info:
                    symbolm = item["symbol"]
                    positionSide = item["positionSide"]
                    # current_pos = float(item['positionAmt'])
                    # 当持仓为多空双向，策略仅为多方向，只处理多方向的仓位
                    # if item['positionSide'] != 'LONG':
                    #     return
                    if symbolm in self.symbols_dict and positionSide == 'BOTH':
                        event = Event(EVENT_POS, {"symbol": symbolm, "pos": item})
                        self.broker.event_engine.put(event)
            else:
                self.dingding(f"注意是不是超并发了或时间不对，{info}", "position")
                self.bugcode(f"get_position:{info}")
        except:
            self.bugcode(traceback, "mrmv_TradeRun_get_position")

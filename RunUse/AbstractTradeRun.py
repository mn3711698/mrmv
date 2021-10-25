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


class TradeRun:

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

        symbol_list = [["AAVEUSDT", 24, 10], ["KSMUSDT", 22, 2], ["UNIUSDT", 27, 42], ["EGLDUSDT", 25.5, 50],
                       ["BNBUSDT", 23, 25], ["SOLUSDT", 25, -10], ["DOTUSDT", 24, 17], ["YFIUSDT", 21, 150],
                       ["ETHUSDT", 26, 80], ["LTCUSDT", 27, 75], ["BCHUSDT", 22, 24], ["MKRUSDT", 24, -10],
                       ["DASHUSDT", 23, -30], ["ZECUSDT", 24, 38], ["ZENUSDT", 24, 49], ["FILUSDT", 21, 34],
                       ["AVAXUSDT", 28, -20], ["LUNAUSDT", 25, -28], ["YFIIUSDT", 24, -41], ["COMPUSDT", 24, -11],
                       ["XMRUSDT", 18, 100], ["TRBUSDT", 21, 118], ["NEOUSDT", 25, 13], ["NEARUSDT", 25, 61],
                       ["ATOMUSDT", 23, 59], ["AXSUSDT", 23, 82], ["ICPUSDT", 24, 150], ["WAVESUSDT", 24, 17],
                       ["LINKUSDT", 22, 5], ["BALUSDT", 22, 46], ["HNTUSDT", 23, 200], ["DYDXUSDT", 22, 100],
                       ["ALICEUSDT", 21, 150], ["SNXUSDT", 26, -30], ["QTUMUSDT", 20, 150], ["RAYUSDT", 26, 150],
                       ["SUSHIUSDT", 23, 295], ["OMGUSDT", 23, 500], ["MASKUSDT", 24, 154], ["UNFIUSDT", 24, -10],
                       ["SRMUSDT", 24, 150], ["GTCUSDT", 24, 74], ["RUNEUSDT", 24, 67], ["BANDUSDT", 25, -39],
                       ["XTZUSDT", 19, -92], ["THETAUSDT", 26, 22], ["KAVAUSDT", 18, 427], ["BTCUSDT", 22, 115]
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
        symbol_list = [["AAVEUSDT", 28, 20], ["KSMUSDT", 27, -10], ["UNIUSDT", 29, 13], ["EGLDUSDT", 30, -20],
                       ["BNBUSDT", 27, 24], ["SOLUSDT", 29, 20], ["DOTUSDT", 29, 95], ["YFIUSDT", 29, 10],
                       ["ETHUSDT", 28, -12], ["LTCUSDT", 29, -13], ["BCHUSDT", 23, -15], ["MKRUSDT", 27, 2],
                       ["DASHUSDT", 29, -15], ["ZECUSDT", 26, 22], ["ZENUSDT", 26, 8], ["FILUSDT", 28, -24],
                       ["AVAXUSDT", 27, -19], ["LUNAUSDT", 21, -20], ["YFIIUSDT", 27, 30], ["COMPUSDT", 27, -6],
                       ["XMRUSDT", 25, 21], ["TRBUSDT", 25, 186], ["NEOUSDT", 28, 20], ["NEARUSDT", 27, 7],
                       ["ATOMUSDT", 24.5, 13], ["AXSUSDT", 27, -30], ["ICPUSDT", 27, -42], ["WAVESUSDT", 25, -20],
                       ["LINKUSDT", 27, -14], ["BALUSDT", 24, -50], ["HNTUSDT", 23, 150], ["DYDXUSDT", 26, 200],
                       ["ALICEUSDT", 23, 150], ["SNXUSDT", 27, 105], ["QTUMUSDT", 27, 150], ["RAYUSDT", 24, 150],
                       ["SUSHIUSDT", 27, 114], ["OMGUSDT", 26, 300], ["MASKUSDT", 24, 350], ["UNFIUSDT", 24, 218],
                       ["SRMUSDT", 26, 65], ["GTCUSDT", 29, 400], ["RUNEUSDT", 25, 126], ["BANDUSDT", 27, 245],
                       ["XTZUSDT", 24, 46], ["THETAUSDT", 25, -22], ["KAVAUSDT", 18, 62], ["BTCUSDT", 22, -62]
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
        symbol_list = [["AAVEUSDT", 31, 4], ["KSMUSDT", 27, 4], ["UNIUSDT", 31.5, 53], ["EGLDUSDT", 30, 10],
                       ["BNBUSDT", 32, 36], ["SOLUSDT", 31, 41], ["DOTUSDT", 30, 25], ["YFIUSDT", 30, 45],
                       ["ETHUSDT", 28, -12], ["LTCUSDT", 29, -12], ["BCHUSDT", 29, 150], ["MKRUSDT", 30, 145],
                       ["DASHUSDT", 29, -10], ["ZECUSDT", 29, 18], ["ZENUSDT", 27, -31], ["FILUSDT", 28, 131],
                       ["AVAXUSDT", 28, -26], ["LUNAUSDT", 27, 59], ["YFIIUSDT", 29, -52], ["COMPUSDT", 27, -41],
                       ["XMRUSDT", 26, 230], ["TRBUSDT", 26, 5], ["NEOUSDT", 28, 38], ["NEARUSDT", 28, -24],
                       ["ATOMUSDT", 25.5, 62], ["AXSUSDT", 28, 67], ["ICPUSDT", 28, 33], ["WAVESUSDT", 25, -41],
                       ["LINKUSDT", 28, 58], ["BALUSDT", 26, 80], ["HNTUSDT", 23, -22], ["DYDXUSDT", 24, 86],
                       ["ALICEUSDT", 24, 100], ["SNXUSDT", 28, 90], ["QTUMUSDT", 24, 62], ["RAYUSDT", 28, -10],
                       ["SUSHIUSDT", 27, -27], ["OMGUSDT", 26, 47], ["MASKUSDT", 25, 178], ["UNFIUSDT", 24, -58],
                       ["SRMUSDT", 25, 155], ["GTCUSDT", 29, -15], ["RUNEUSDT", 28, 42], ["BANDUSDT", 30, 183],
                       ["XTZUSDT", 25, 200], ["THETAUSDT", 29, 189], ["KAVAUSDT", 24, 85], ["BTCUSDT", 30, -25]
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
        symbol_list = [["AAVEUSDT", 32, 15], ["KSMUSDT", 27, 12], ["UNIUSDT", 26, -10], ["EGLDUSDT", 30, 50],
                       ["BNBUSDT", 35, -20], ["SOLUSDT", 31, 91], ["DOTUSDT", 30, 50], ["YFIUSDT", 35, 90],
                       ["ETHUSDT", 33, -5], ["LTCUSDT", 30, -25], ["BCHUSDT", 30, -5], ["MKRUSDT", 32, -22],
                       ["DASHUSDT", 31, -8], ["ZECUSDT", 27, 6], ["ZENUSDT", 28, 68], ["FILUSDT", 29, 40],
                       ["AVAXUSDT", 28, 44], ["LUNAUSDT", 28, 178], ["YFIIUSDT", 29, 83], ["COMPUSDT", 30, -21],
                       ["XMRUSDT", 25, -39], ["TRBUSDT", 28, 84], ["NEOUSDT", 28, -3], ["NEARUSDT", 28, 69],
                       ["ATOMUSDT", 27, -20], ["AXSUSDT", 29, 166], ["ICPUSDT", 28, 220], ["WAVESUSDT", 27, 75],
                       ["LINKUSDT", 29, 57], ["BALUSDT", 27, 110], ["HNTUSDT", 28, 14], ["DYDXUSDT", 28, 60],
                       ["ALICEUSDT", 24, 60], ["SNXUSDT", 28, 22], ["QTUMUSDT", 27, -11], ["RAYUSDT", 28, -38],
                       ["SUSHIUSDT", 27, 245], ["OMGUSDT", 26, 113], ["MASKUSDT", 26, 111], ["UNFIUSDT", 24, 94],
                       ["SRMUSDT", 27, 80], ["GTCUSDT", 28, 72], ["RUNEUSDT", 28, 55], ["BANDUSDT", 30, 80],
                       ["XTZUSDT", 27, -23], ["THETAUSDT", 28, 44], ["KAVAUSDT", 27, 38], ["BTCUSDT", 25, 71]
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

        symbol_list = [["AAVEUSDT", 31, 10], ["KSMUSDT", 27, 2], ["UNIUSDT", 27, 15], ["EGLDUSDT", 30, 50],
                       ["BNBUSDT", 32, 40], ["SOLUSDT", 31, 5], ["DOTUSDT", 30, 100], ["YFIUSDT", 33, 90],
                       ["ETHUSDT", 33, -4], ["LTCUSDT", 29, 70], ["BCHUSDT", 32, -10], ["MKRUSDT", 31, 22],
                       ["DASHUSDT", 30, 18], ["ZECUSDT", 30, 153], ["ZENUSDT", 31, 55], ["FILUSDT", 30, 68],
                       ["AVAXUSDT", 29, 78], ["LUNAUSDT", 28, 78], ["YFIIUSDT", 30, 14], ["COMPUSDT", 30, 22],
                       ["XMRUSDT", 30, 44], ["TRBUSDT", 29, 78], ["NEOUSDT", 29, 30], ["NEARUSDT", 30, 71],
                       ["ATOMUSDT", 28, -19], ["AXSUSDT", 30, 51], ["ICPUSDT", 30, 77], ["WAVESUSDT", 28, 101],
                       ["LINKUSDT", 29, 22], ["BALUSDT", 28, 39], ["HNTUSDT", 29, 83], ["DYDXUSDT", 28, 190],
                       ["ALICEUSDT", 28, 100], ["SNXUSDT", 27, 27], ["QTUMUSDT", 27, 46], ["RAYUSDT", 28, 125],
                       ["SUSHIUSDT", 27, 52], ["OMGUSDT", 26, -14], ["MASKUSDT", 26, 90], ["UNFIUSDT", 26, 92],
                       ["SRMUSDT", 28, 59], ["GTCUSDT", 28, 175], ["RUNEUSDT", 28, 44], ["BANDUSDT", 30, 30],
                       ["XTZUSDT", 29, -7], ["THETAUSDT", 27, 38], ["KAVAUSDT", 28, 57], ["BTCUSDT", 25, 68]
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

        symbol_list = [["AAVEUSDT", 30, 10], ["KSMUSDT", 29, 50], ["UNIUSDT", 30, 10], ["EGLDUSDT", 32, 20],
                       ["BNBUSDT", 31, 50], ["SOLUSDT", 33, 20], ["DOTUSDT", 30, 42], ["YFIUSDT", 34, 90],
                       ["ETHUSDT", 32, 40], ["LTCUSDT", 32, 80], ["BCHUSDT", 31, 33], ["MKRUSDT", 31, 24],
                       ["DASHUSDT", 30, 23], ["ZECUSDT", 30, 45], ["ZENUSDT", 30, 21], ["FILUSDT", 29, 63],
                       ["AVAXUSDT", 29, 10], ["LUNAUSDT", 30, 23], ["YFIIUSDT", 32, 31], ["COMPUSDT", 31, 34],
                       ["XMRUSDT", 31, 24], ["TRBUSDT", 30, 5], ["NEOUSDT", 30, 26], ["NEARUSDT", 30, 15],
                       ["ATOMUSDT", 29, 40], ["AXSUSDT", 32, 100], ["ICPUSDT", 31, 64], ["WAVESUSDT", 28, 1],
                       ["LINKUSDT", 29, 12], ["BALUSDT", 29, 91], ["HNTUSDT", 31, 16], ["DYDXUSDT", 30, 4],
                       ["ALICEUSDT", 29, 75], ["SNXUSDT", 27, -14], ["QTUMUSDT", 27, 14], ["RAYUSDT", 26, -25],
                       ["SUSHIUSDT", 31, 21], ["OMGUSDT", 26, 101], ["MASKUSDT", 26, 38], ["UNFIUSDT", 26, 81],
                       ["SRMUSDT", 28, 115], ["GTCUSDT", 28, 79], ["RUNEUSDT", 28, 89], ["BANDUSDT", 30, 29],
                       ["XTZUSDT", 30, 54], ["THETAUSDT", 26, 34], ["KAVAUSDT", 30, 12], ["BTCUSDT", 25, 119, 3]
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

        symbol_list = [["AAVEUSDT", 32, 10], ["KSMUSDT", 30, 18], ["UNIUSDT", 32, 10], ["EGLDUSDT", 35, -10],
                       ["BNBUSDT", 31, 100], ["SOLUSDT", 33, 30], ["DOTUSDT", 31, 50], ["YFIUSDT", 33, 45],
                       ["ETHUSDT", 32, 150], ["LTCUSDT", 34, 140], ["BCHUSDT", 30, 115], ["MKRUSDT", 34, 39],
                       ["DASHUSDT", 31, 62], ["ZECUSDT", 30, 45], ["ZENUSDT", 32, 9], ["FILUSDT", 30, 54],
                       ["AVAXUSDT", 33, 14], ["LUNAUSDT", 30, 9], ["YFIIUSDT", 32, 6], ["COMPUSDT", 32, 21],
                       ["XMRUSDT", 32, 64], ["TRBUSDT", 31, 5], ["NEOUSDT", 33, 150], ["NEARUSDT", 32, -21],
                       ["ATOMUSDT", 31, 22], ["AXSUSDT", 32, 82], ["ICPUSDT", 28, 22], ["WAVESUSDT", 32, 24],
                       ["LINKUSDT", 30, 50], ["BALUSDT", 30, 42], ["HNTUSDT", 32, 30], ["DYDXUSDT", 30, 150],
                       ["ALICEUSDT", 30, 80], ["SNXUSDT", 27, -1], ["QTUMUSDT", 27, 70], ["RAYUSDT", 28, -40],
                       ["SUSHIUSDT", 31, 21], ["OMGUSDT", 28, 76], ["MASKUSDT", 30, 3], ["UNFIUSDT", 26, 10],
                       ["SRMUSDT", 28, -4], ["GTCUSDT", 28, 57], ["RUNEUSDT", 28, 70], ["BANDUSDT", 30, 21],
                       ["XTZUSDT", 30, 42], ["THETAUSDT", 29, -21], ["KAVAUSDT", 30, -10], ["BTCUSDT", 25, 16]
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

        symbol_list = [["AAVEUSDT", 32, -4], ["KSMUSDT", 31, 17], ["UNIUSDT", 31, 15], ["EGLDUSDT", 33, 20],
                       ["BNBUSDT", 31, 100], ["SOLUSDT", 33, 20], ["DOTUSDT", 35, 100], ["YFIUSDT", 33, 19],
                       ["ETHUSDT", 33, 52], ["LTCUSDT", 33, 70], ["BCHUSDT", 31, 12], ["MKRUSDT", 35, 12],
                       ["DASHUSDT", 31, 4], ["ZECUSDT", 33, 58], ["ZENUSDT", 33, 22], ["FILUSDT", 35, -9],
                       ["AVAXUSDT", 35, -18], ["LUNAUSDT", 35, 55], ["YFIIUSDT", 34, 30], ["COMPUSDT", 34, 6],
                       ["XMRUSDT", 33, 22], ["TRBUSDT", 34, 5], ["NEOUSDT", 34, 31], ["NEARUSDT", 32, 25],
                       ["ATOMUSDT", 32, 18], ["AXSUSDT", 35, 6], ["ICPUSDT", 28, 70], ["WAVESUSDT", 35, -38],
                       ["LINKUSDT", 35, 79], ["BALUSDT", 32, -5], ["HNTUSDT", 32, -50], ["DYDXUSDT", 32, 150],
                       ["ALICEUSDT", 34, 100], ["SNXUSDT", 27, 109], ["QTUMUSDT", 27, 50], ["RAYUSDT", 30, -40],
                       ["SUSHIUSDT", 31, 56], ["OMGUSDT", 28, -8], ["MASKUSDT", 30, 3], ["UNFIUSDT", 27, 111],
                       ["SRMUSDT", 28, 100], ["GTCUSDT", 28, 55], ["RUNEUSDT", 28, -12], ["BANDUSDT", 30, 40],
                       ["XTZUSDT", 30, 32], ["THETAUSDT", 30, 65], ["KAVAUSDT", 30, -14], ["BTCUSDT", 25, 299]
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

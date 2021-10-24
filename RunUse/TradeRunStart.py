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


class TradeRunStart:

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
        symbol_list = [["ARUSDT", 23, -68], ["CELOUSDT", 25, -62], ["RLCUSDT", 24, 14], ["LITUSDT", 23, 199],
                       ["C98USDT", 25, 28], ["MTLUSDT", 24, 350], ["1INCHUSDT", 27, -11], ["CRVUSDT", 21, 650],
                       ["SXPUSDT", 27, 58], ["AUDIOUSDT", 27, 200], ["TOMOUSDT", 28, 220], ["ADAUSDT", 23, 150],
                       ["ICXUSDT", 23, 41], ["BAKEUSDT", 22, -7], ["BELUSDT", 23, 32], ["ALGOUSDT", 23, 71],
                       ["CTKUSDT", 22, 110], ["KNCUSDT", 28, 31], ["ENJUSDT", 25, 33], ["FTMUSDT", 26, 350],
                       ["DODOUSDT", 25, 350], ["MATICUSDT", 23, -20], ["IOTAUSDT", 20, 200], ["STORJUSDT", 25, 98],
                       ["XRPUSDT", 27, -1], ["RENUSDT", 23, 45], ["SFPUSDT", 26, -23], ["ZRXUSDT", 22, 150],
                       ["ALPHAUSDT", 22, 85], ["ATAUSDT", 28, -10], ["ONTUSDT", 21, 200], ["OGNUSDT", 25, 100],
                       ["SANDUSDT", 23, 200], ["MANAUSDT", 26, -50], ["GRTUSDT", 24, 21], ["OCEANUSDT", 23, 35],
                       ["BATUSDT", 23, 52], ["CVCUSDT", 22, -3], ["FLMUSDT", 25, 200], ["KEEPUSDT", 24, 200]
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

        symbol_list = [["ARUSDT", 24, 400], ["CELOUSDT", 22, 41], ["RLCUSDT", 25, -25], ["LITUSDT", 25, 68],
                       ["C98USDT", 31, 250], ["MTLUSDT", 23, -41], ["1INCHUSDT", 27, -4], ["CRVUSDT", 23, 10],
                       ["SXPUSDT", 27, 474], ["AUDIOUSDT", 29, -60], ["TOMOUSDT", 28, 150], ["ADAUSDT", 27, 50],
                       ["ICXUSDT", 23, 120], ["BAKEUSDT", 28, -32], ["BELUSDT", 27, 250], ["ALGOUSDT", 26, 100],
                       ["CTKUSDT", 26, 12], ["KNCUSDT", 26, 160], ["ENJUSDT", 28, 18], ["FTMUSDT", 29, 64],
                       ["DODOUSDT", 26, 150], ["MATICUSDT", 28, 100], ["IOTAUSDT", 20, 1], ["STORJUSDT", 25, -60],
                       ["XRPUSDT", 23, -34], ["RENUSDT", 27, 20], ["SFPUSDT", 21, 60], ["ZRXUSDT", 24, -8],
                       ["ALPHAUSDT", 24, 21], ["ATAUSDT", 28, 140], ["ONTUSDT", 28, 50], ["OGNUSDT", 24, 32],
                       ["SANDUSDT", 26, -45], ["MANAUSDT", 29, 92], ["GRTUSDT", 22, -50], ["OCEANUSDT", 24, 100],
                       ["BATUSDT", 23, 30], ["CVCUSDT", 24, 110], ["FLMUSDT", 26, -20], ["KEEPUSDT", 28, 50]
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

        symbol_list = [["ARUSDT", 24, 350], ["CELOUSDT", 24, -52], ["RLCUSDT", 29, 42], ["LITUSDT", 26, 43],
                       ["C98USDT", 30, 250], ["MTLUSDT", 31, 130], ["1INCHUSDT", 26, 44], ["CRVUSDT", 25, 8],
                       ["SXPUSDT", 27, 133], ["AUDIOUSDT", 28, 15], ["TOMOUSDT", 29, 5], ["ADAUSDT", 25, 150],
                       ["ICXUSDT", 25.5, -28], ["BAKEUSDT", 23, -4], ["BELUSDT", 28, 37], ["ALGOUSDT", 27, 95],
                       ["CTKUSDT", 26, 35], ["KNCUSDT", 27, 53], ["ENJUSDT", 28, 35], ["FTMUSDT", 29, -13],
                       ["DODOUSDT", 28, 150], ["MATICUSDT", 28, 120], ["IOTAUSDT", 27, 28], ["STORJUSDT", 22, 90],
                       ["XRPUSDT", 29, 35], ["RENUSDT", 28, 63], ["SFPUSDT", 25, -55], ["ZRXUSDT", 24, -4],
                       ["ALPHAUSDT", 26, 63], ["ATAUSDT", 28, -20], ["ONTUSDT", 28, 100], ["OGNUSDT", 24, -35],
                       ["SANDUSDT", 29, -33], ["MANAUSDT", 29, -10], ["GRTUSDT", 20, 250], ["OCEANUSDT", 25.5, -10],
                       ["BATUSDT", 32, -20], ["CVCUSDT", 25, 94], ["FLMUSDT", 27, 85], ["KEEPUSDT", 28, 150]
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

        symbol_list = [["ARUSDT", 27, 165], ["CELOUSDT", 27, 136], ["RLCUSDT", 29, 88], ["LITUSDT", 29, 109],
                       ["C98USDT", 30, 36], ["MTLUSDT", 29, 95], ["1INCHUSDT", 26, 100], ["CRVUSDT", 24, 10],
                       ["SXPUSDT", 27, 85], ["AUDIOUSDT", 29, 100], ["TOMOUSDT", 26, 100], ["ADAUSDT", 26, 100],
                       ["ICXUSDT", 27, -8], ["BAKEUSDT", 28, 200], ["BELUSDT", 28, 50], ["ALGOUSDT", 28, 110],
                       ["CTKUSDT", 27, 21], ["KNCUSDT", 29, 95], ["ENJUSDT", 28, 54], ["FTMUSDT", 29, 92],
                       ["DODOUSDT", 28, -10], ["MATICUSDT", 27, 100], ["IOTAUSDT", 25, -45], ["STORJUSDT", 26, -5],
                       ["XRPUSDT", 26, -25], ["RENUSDT", 28, 104], ["SFPUSDT", 25, 150], ["ZRXUSDT", 26, 20],
                       ["ALPHAUSDT", 25, 43], ["ATAUSDT", 28, 160], ["ONTUSDT", 28, -27], ["OGNUSDT", 27, -30],
                       ["SANDUSDT", 30, -9], ["MANAUSDT", 26, -5], ["GRTUSDT", 23, 300], ["OCEANUSDT", 28, 62],
                       ["BATUSDT", 31, 53], ["CVCUSDT", 27, -38], ["FLMUSDT", 28, 90], ["KEEPUSDT", 28, 85]
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

        symbol_list = [["ARUSDT", 27, 143], ["CELOUSDT", 31, 37], ["RLCUSDT", 29, 88], ["LITUSDT", 30, 94],
                       ["C98USDT", 30, 300], ["MTLUSDT", 30, 120], ["1INCHUSDT", 26, 136], ["CRVUSDT", 27, -28],
                       ["SXPUSDT", 27, 81], ["AUDIOUSDT", 30, 350], ["TOMOUSDT", 27, 72], ["ADAUSDT", 27, 25],
                       ["ICXUSDT", 30, 51], ["BAKEUSDT", 31, 42], ["BELUSDT", 28, 85], ["ALGOUSDT", 30, 34],
                       ["CTKUSDT", 27, -11], ["KNCUSDT", 30, 66], ["ENJUSDT", 29, 97], ["FTMUSDT", 29, 31],
                       ["DODOUSDT", 29, 30], ["MATICUSDT", 30, 52], ["IOTAUSDT", 25, -20], ["STORJUSDT", 28, 130],
                       ["XRPUSDT", 26, 100], ["RENUSDT", 31, 62], ["SFPUSDT", 25, 58], ["ZRXUSDT", 25, 50],
                       ["ALPHAUSDT", 26, 230], ["ATAUSDT", 29, 76], ["ONTUSDT", 28, 53], ["OGNUSDT", 30, 85],
                       ["SANDUSDT", 29, 35], ["MANAUSDT", 31, 43], ["GRTUSDT", 23, -10], ["OCEANUSDT", 28, -23],
                       ["BATUSDT", 31, 130], ["CVCUSDT", 30, 55], ["FLMUSDT", 28, 77], ["KEEPUSDT", 29, 57]
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

        symbol_list = [["ARUSDT", 30, 98], ["CELOUSDT", 33, 20], ["RLCUSDT", 29, -23], ["LITUSDT", 31, 63],
                       ["C98USDT", 30, 32], ["MTLUSDT", 31, 70], ["1INCHUSDT", 26, 56], ["CRVUSDT", 27, 58],
                       ["SXPUSDT", 27, -2], ["AUDIOUSDT", 30, 200], ["TOMOUSDT", 27, -7], ["ADAUSDT", 29, 50],
                       ["ICXUSDT", 30, 26], ["BAKEUSDT", 31, 46], ["BELUSDT", 29, 31], ["ALGOUSDT", 31, 32],
                       ["CTKUSDT", 27, -15], ["KNCUSDT", 30, 105], ["ENJUSDT", 30, -18], ["FTMUSDT", 31, 17],
                       ["DODOUSDT", 29, 70], ["MATICUSDT", 30, 35], ["IOTAUSDT", 33, -22], ["STORJUSDT", 27, 43],
                       ["XRPUSDT", 27, 65], ["RENUSDT", 31, 38], ["SFPUSDT", 29, 50], ["ZRXUSDT", 26, 39],
                       ["ALPHAUSDT", 26, 50], ["ATAUSDT", 29, -15], ["ONTUSDT", 28, 52], ["OGNUSDT", 30, 43],
                       ["SANDUSDT", 29, 33], ["MANAUSDT", 31, -15], ["GRTUSDT", 25, -30], ["OCEANUSDT", 30, 50],
                       ["BATUSDT", 30, 36], ["CVCUSDT", 31, 47], ["FLMUSDT", 27, 21], ["KEEPUSDT", 30, 75]
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

        symbol_list = [["ARUSDT", 31, 16], ["CELOUSDT", 30, 50], ["RLCUSDT", 29, -20], ["LITUSDT", 32, 92],
                       ["C98USDT", 34, 24], ["MTLUSDT", 34, 55], ["1INCHUSDT", 26, 75], ["CRVUSDT", 29, -12],
                       ["SXPUSDT", 27, -11], ["AUDIOUSDT", 31, -20], ["TOMOUSDT", 27, -20], ["ADAUSDT", 31, 100],
                       ["ICXUSDT", 31, 15], ["BAKEUSDT", 31, 47], ["BELUSDT", 31, 51], ["ALGOUSDT", 31, 46],
                       ["CTKUSDT", 30, 29], ["KNCUSDT", 29, 55], ["ENJUSDT", 30, 91], ["FTMUSDT", 32, 28],
                       ["DODOUSDT", 30, 31], ["MATICUSDT", 32, 50], ["IOTAUSDT", 33, -10], ["STORJUSDT", 28, 60],
                       ["XRPUSDT", 27, 36], ["RENUSDT", 31, 93], ["SFPUSDT", 29, 78], ["ZRXUSDT", 30, 65],
                       ["ALPHAUSDT", 27, 93], ["ATAUSDT", 31, 200], ["ONTUSDT", 31, 63],  ["OGNUSDT", 25, 50],
                       ["SANDUSDT", 29, 50], ["MANAUSDT", 31, 65], ["GRTUSDT", 26, 50], ["OCEANUSDT", 27, 70],
                       ["BATUSDT", 30, 75], ["CVCUSDT", 31, 55], ["FLMUSDT", 27, 72], ["KEEPUSDT", 34, 75]
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

        symbol_list = [["ARUSDT", 31, 16], ["CELOUSDT", 30, 50], ["RLCUSDT", 29, 26], ["LITUSDT", 33, 91],
                       ["C98USDT", 34, 24], ["MTLUSDT", 34, 15], ["1INCHUSDT", 29, 80], ["CRVUSDT", 29, 37],
                       ["SXPUSDT", 27, -24], ["AUDIOUSDT", 34, -7], ["TOMOUSDT", 32, 35], ["ADAUSDT", 31, 30],
                       ["ICXUSDT", 32, 13], ["BAKEUSDT", 35, 12], ["BELUSDT", 31, 110], ["ALGOUSDT", 31, 35],
                       ["CTKUSDT", 30, 89], ["KNCUSDT", 29, 63], ["ENJUSDT", 31, 45], ["FTMUSDT", 33, 45],
                       ["DODOUSDT", 34, 77], ["MATICUSDT", 32, 39], ["IOTAUSDT", 33, 75], ["STORJUSDT", 31, 60],
                       ["XRPUSDT", 27, 150], ["RENUSDT", 32, -10], ["SFPUSDT", 30, 52], ["ZRXUSDT", 30, 89],
                       ["ALPHAUSDT", 35, 55], ["ATAUSDT", 33, 150], ["ONTUSDT", 27, 130], ["OGNUSDT", 32, 40],
                       ["SANDUSDT", 29, 23], ["MANAUSDT", 35, 32], ["GRTUSDT", 26, 50], ["OCEANUSDT", 30, -12],
                       ["BATUSDT", 30, -10], ["CVCUSDT", 29, 73], ["FLMUSDT", 31, 63], ["KEEPUSDT", 34, 75]
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

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


class AbstractTradeRun:

    def __init__(self, symbols_conf):
        self.min_volume_dict = {}
        self.symbols_list = []
        self.symbols_dict = {}
        self.trading_size_dict = {}
        self.kline_time_dict = {}
        self.symbol_interval_dict = {}
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

    def conf_initialize(self, symbol_metas):
        # 初始化dict
        # [symbol, trading_size, win_arg, add_arg]
        for symbol, meta in symbol_metas.item():
            self.symbols_list.append(symbol)
            self.symbols_dict[symbol] = [meta['win_arg'], meta['add_arg']]
            self.trading_size_dict[symbol] = meta['trading_size']
            self.symbol_interval_dict[symbol] = meta['interval']

    def initialization_data(self):
        try:
            binance_http = BinanceFutureHttp(key=self.key, secret=self.secret)
            exchange_infos = binance_http.exchangeInfo()
            if isinstance(exchange_infos, dict):
                exchange_symbol_infos = exchange_infos['symbols']
                for exchange_symbol_info in exchange_symbol_infos:
                    _symbol = exchange_symbol_info['symbol']
                    if _symbol in self.trading_size_dict:
                        for j in exchange_symbol_info['filters']:
                            if j['filterType'] == 'LOT_SIZE':
                                min_qty = float(j['minQty'])
                                trading_size = self.trading_size_dict[_symbol]
                                if min_qty > trading_size:
                                    self.trading_size_dict[_symbol] = min_qty
                                    msg = f"config里的symbol:{_symbol},trading_size:{trading_size},太小,minQty{min_qty}"
                                    self.bugcode(msg)
                                self.min_volume_dict[_symbol] = min_qty
        except:
            self.bugcode(traceback, "mrmv_TradeRun_initialization_data")

    def get_line_1min(self):
        minute_3 = self.get_minute_numbers(3)
        minute_5 = self.get_minute_numbers(5)
        minute_15 = self.get_minute_numbers(15)
        minute_30 = self.get_minute_numbers(30)
        hour_2 = self.get_hour_numbers(2)
        hour_4 = self.get_hour_numbers(4)

        bought = 75
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '1m'
        self.get_line('minute_1', bought, sold_bar, bought_bar, exchange_interval)

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
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '3m'
        self.get_line('minute_3', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_5min(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '5m'
        self.get_line('minute_5', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_15min(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '15m'
        self.get_line('minute_15', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_30min(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '30m'
        self.get_line('minute_30', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_1h(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '1h'
        self.get_line('hour_1', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_2h(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '2h'
        self.get_line('hour_2', bought, sold_bar, bought_bar, exchange_interval)

    def get_line_4h(self):
        bought = 70
        sold_bar = 10
        bought_bar = 10
        exchange_interval = '4h'
        self.get_line('hour_4', bought, sold_bar, bought_bar, exchange_interval)

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

    def get_line(self, interval: str, bought: int, sold_bar: int, bought_bar: int, exchange_interval: str):
        for symbol, interval_config_dict in self.symbol_interval_dict.items():
            interval_config = interval_config_dict[interval]
            sold = interval_config['sold']
            contrast = interval_config['contrast']
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, exchange_interval, contrast)
            if not flag:
                time.sleep(self.time_stop)
                self.bugcode(f"get_line_1min:{symbol},{exchange_interval}")
                flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, exchange_interval, contrast)
            time.sleep(self.time_stop)

    @staticmethod
    def get_minute_numbers(step: int):
        return [str(i).zfill(2) for i in range(0, 60, step)]

    @staticmethod
    def get_hour_numbers(step: int):
        return [str(i).zfill(2) for i in range(0, 24, step)]

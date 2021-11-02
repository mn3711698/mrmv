# -*- coding: utf-8 -*-
##############################################################################
# Author：QQ173782910
##############################################################################

import time
import traceback
from decimal import Decimal
from typing import Dict, List

from RunUse.model.symbol_position import SymbolPosition
from getaway.redis_wrapper_binance_http import RedisWrapperBinanceFutureHttp
from utils.brokers import Broker
from getaway.binance_http import BinanceFutureHttp
from getaway.send_msg import bugcode, getToday, dingding
from constant.constant import (EVENT_POS, EVENT_KLINE)
from utils.event import EventEngine, Event
from strategies.LineWith import LineWith
from config import key, secret, redisc, kline_source, trade_klines_fetch_worker, trade_size_factor, redis_namespace, \
    record_trade
from concurrent.futures.thread import ThreadPoolExecutor


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
        self.time_stop = 2
        self.key = key
        self.secret = secret

        self.engine = EventEngine()

        if kline_source == 'redis':
            self.binance_http = RedisWrapperBinanceFutureHttp(redisc, redis_namespace, self.key, self.secret)
            self.broker = Broker(self.engine, binance_http=self.binance_http, key=self.key, secret=self.secret,
                                 symbols_list=self.symbols_list)
            self.backup_binance_http = BinanceFutureHttp(key=self.key, secret=self.secret)

        elif kline_source == 'web':
            self.broker = Broker(self.engine, key=self.key, secret=self.secret, symbols_list=self.symbols_list)
            self.binance_http = self.broker.binance_http
            self.backup_binance_http = self.binance_http

        self.initialization_data()
        self.broker.add_strategy(LineWith, self.symbols_dict, self.min_volume_dict, self.trading_size_dict)

    def conf_initialize(self, symbol_metas):
        # 初始化dict
        # [symbol, trading_size, win_arg, add_arg]
        for symbol, meta in symbol_metas.items():
            self.symbols_list.append(symbol)
            self.symbols_dict[symbol] = [meta['win_arg'], meta['add_arg']]
            self.symbol_interval_dict[symbol] = meta['interval']

            config_trading_size = meta['trading_size']
            precision = self.calculate_precision(config_trading_size)
            trading_size = Decimal(str(config_trading_size)) * Decimal(trade_size_factor)
            if precision > 0:
                quantize_format = '0.' + int(precision) * '0'
                trading_size = trading_size.quantize(Decimal(quantize_format))
            trading_size = float(trading_size)

            self.trading_size_dict[symbol] = trading_size

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

    def get_kline_data(self, symbol, sold, bought, sold_bar, bought_bar, interval, contrast, backup=False):
        if not backup:
            binance_http = self.broker.binance_http
        else:
            binance_http = self.backup_binance_http

        try:
            if symbol in self.symbols_dict:
                try:
                    data = binance_http.get_kline_interval(symbol=symbol, interval=interval, limit=100)
                except Exception as e:
                    # self.bugcode(f"{symbol},{interval},get_kline_data:{e}")
                    # print(e)
                    data = binance_http.get_kline_interval(symbol=symbol, interval=interval, limit=100)
                if isinstance(data, list):
                    if len(data):
                        kline_time = data[-1][0]
                        if kline_time != self.kline_time_dict.get(symbol + interval, 0):
                            edata = {'symbol': symbol, "data": data, "sold": sold, "bought": bought,
                                     "sold_bar": sold_bar, "bought_bar": bought_bar, 'interval': interval,
                                     "contrast": contrast}
                            event = Event(EVENT_KLINE, edata)
                            self.broker.event_engine.put(event)
                            self.kline_time_dict[symbol + interval] = kline_time
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
        futures = []
        with ThreadPoolExecutor(max_workers=trade_klines_fetch_worker) as tp:
            for symbol, interval_config_dict in self.symbol_interval_dict.items():
                interval_config = interval_config_dict[interval]
                future = tp.submit(self.get_line0, symbol, interval_config,
                                   bought, sold_bar, bought_bar, exchange_interval)
                futures.append(future)
        [future.result() for future in futures]

    def get_line0(self, symbol: str, interval_config: Dict[str, int], bought: int, sold_bar: int, bought_bar: int,
                  exchange_interval: str):
        sold = interval_config['sold']
        contrast = interval_config['contrast']
        flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, exchange_interval, contrast)
        query_times = 0
        while not flag:
            if query_times > 10:
                self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, exchange_interval, contrast, True)
                break
            query_times = query_times + 1
            time.sleep(self.time_stop)
            self.bugcode(f"get_line_1min:{symbol},{exchange_interval}")
            flag = self.get_kline_data(symbol, sold, bought, sold_bar, bought_bar, exchange_interval, contrast)
        time.sleep(self.time_stop)

    def record_position(self, symbol_position: SymbolPosition):
        pass

    def query_position(self, symbols: List[str], start_time: int = None, end_time: int = None) \
            -> Dict[str, List[SymbolPosition]]:
        pass

    @staticmethod
    def calculate_precision(number):
        number_str = str(number)
        if number_str.__contains__('.'):
            precision = len(number_str) - number_str.index('.') - 1
        else:
            precision = 0
        return precision

    @staticmethod
    def get_minute_numbers(step: int):
        return [str(i).zfill(2) for i in range(0, 60, step)]

    @staticmethod
    def get_hour_numbers(step: int):
        return [str(i).zfill(2) for i in range(0, 24, step)]

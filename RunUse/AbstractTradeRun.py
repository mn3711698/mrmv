# -*- coding: utf-8 -*-
##############################################################################
# Author：QQ173782910
##############################################################################
import json
import time
import traceback
from collections import defaultdict
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
    record_trade, trade_record_namespace, leverage, timezone, get_symbol_metas
from concurrent.futures.thread import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler


def get_minute_numbers(step: int):
    return [str(i).zfill(2) for i in range(0, 60, step)]


def get_hour_numbers(step: int):
    return [str(i).zfill(2) for i in range(0, 24, step)]


class AbstractTradeRun:

    interval_map = {
        'minute': {
            '1m': get_minute_numbers(1),
            '3m': get_minute_numbers(3),
            '5m': get_minute_numbers(5),
            '15m': get_minute_numbers(15),
            '30m': get_minute_numbers(30)
        },
        'hour': {
            '1h': get_hour_numbers(1)
        }
    }

    def __init__(self, config: dict, group_name: str = None):
        symbol_metas = get_symbol_metas(group_name)
        self._config = config
        self.min_volume_dict = {}
        self.symbols_list = []
        self.symbols_dict = {}
        self.trading_size_dict = {}
        self.kline_time_dict = {}
        self.symbol_interval_dict = {}
        self.redisc = redisc
        self.conf_initialize(symbol_metas)
        self.interval_metas = self._config['trade']['strategy']['interval_metas']
        self.bugcode = bugcode
        self.getToday = getToday
        self.dingding = dingding
        self.min_volume = 0.001
        self.time_stop = 2
        self.key = key
        self.secret = secret

        self.engine = EventEngine()
        self.scheduler = BackgroundScheduler(timezone=timezone)

        if kline_source == 'redis':
            self.binance_http = RedisWrapperBinanceFutureHttp(timezone, redisc, redis_namespace,
                                                              key=self.key, secret=self.secret)
            self.broker = Broker(timezone, self.engine, binance_http=self.binance_http,
                                 key=self.key, secret=self.secret,
                                 symbols_list=self.symbols_list)
            self.backup_binance_http = BinanceFutureHttp(timezone, key=self.key, secret=self.secret)

        elif kline_source == 'web':
            self.broker = Broker(timezone, self.engine,
                                 key=self.key, secret=self.secret, symbols_list=self.symbols_list)
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
            binance_http = self.binance_http
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
            for _symbol in self.trading_size_dict.keys():
                self.binance_http.set_leverage(_symbol, leverage)
        except Exception as e:
            self.bugcode(traceback, "mrmv_TradeRun_initialization_data")

    def _trade_on_interval(self, interval: str):
        ti = self.getToday(2)
        h, m = ti.split(':')
        if interval in self.interval_map['hour']:
            if h not in self.interval_map['hour'][interval]:
                return
            if int(m) != 0:
                return
        elif interval in self.interval_map['minute']:
            if m not in self.interval_map['minute'][interval]:
                return
        else:
            raise Exception(f'unsupported interval: {interval}')
        print(f'time: {ti}, interval: {interval} trade process')
        self._trade_on_interval0(interval)

    def _trade_on_interval0(self, interval: str):
        interval_meta = self.interval_metas[interval]
        bought = interval_meta['bought']
        bought_bar = interval_meta['bought_bar']
        self.get_line(interval, bought, bought_bar)

    def _register_position_fetcher(self):
        self.scheduler.add_job(self.get_position, trigger='cron', id='trade_get_position', second='*/10')

    def _register_intervals_from_config(self):
        intervals = self._config['trade']['intervals']
        for interval in intervals:
            self._register_interval(interval)

    def _register_interval(self, interval: str):
        self.scheduler.add_job(self._trade_on_interval,
                               trigger='cron', id=f'trade_{interval}', second='2', args=[interval])

    def start(self):
        self._register_position_fetcher()
        self._register_intervals_from_config()
        self.scheduler.start()

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

    def get_line(self, interval: str, bought: int, bought_bar: int):
        futures = []
        with ThreadPoolExecutor(max_workers=trade_klines_fetch_worker) as tp:
            for symbol, interval_config_dict in self.symbol_interval_dict.items():
                interval_config = interval_config_dict[interval]
                future = tp.submit(self.get_line0, symbol, interval_config,
                                   bought, bought_bar, interval)
                futures.append(future)
        [future.result() for future in futures]

    def get_line0(self, symbol: str, interval_config: Dict[str, int], bought: int, bought_bar: int,
                  exchange_interval: str):
        sold = interval_config['sold']
        sold_bar = interval_config['sold_bar']
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
        if record_trade:
            record_key = ':'.join([trade_record_namespace, symbol_position.symbol])
            self.redisc.zadd(record_key, {json.dumps(symbol_position.__dict__): symbol_position.timestamp})

    def query_position(self, symbols: List[str], start_time: int = None, end_time: int = None) \
            -> Dict[str, List[SymbolPosition]]:
        positions_map = defaultdict(list)
        for symbol in symbols:
            record_key = ':'.join([trade_record_namespace, symbol])
            position_dict_bs = self.redisc.zrangebyscore(record_key, start_time, end_time, start=0, num=9999999)
            position_dicts = [json.loads(str(position_dict, encoding='utf-8')) for position_dict in position_dict_bs]
            positions = []
            for position_dict in position_dicts:
                position = SymbolPosition()
                position.__dict__ = position_dict
                positions.append(position)
            positions_map[symbol] = positions
        return positions_map

    @staticmethod
    def calculate_precision(number):
        number_str = str(number)
        if number_str.__contains__('.'):
            precision = len(number_str) - number_str.index('.') - 1
        else:
            precision = 0
        return precision

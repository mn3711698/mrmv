# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################
import json

from redis import StrictRedis

from KlinePush import get_kline_key_name
from getaway.binance_http import BinanceFutureHttp


class RedisWrapperBinanceFutureHttp(BinanceFutureHttp):

    def __init__(self, redisc: StrictRedis, key=None, secret=None, host=None, timeout=30):
        super().__init__(key, secret, host, timeout)
        self.redisc = redisc

    def get_kline_interval(self, symbol, interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        _b_klines = []
        if start_time is None and end_time is None:
            start_time = '-inf'
            end_time = '+inf'
            _b_klines = self.redisc.zrevrangebyscore(get_kline_key_name(interval, symbol), end_time, start_time,
                                                     start=0, num=limit)
            _b_klines.reverse()
        elif start_time is None and end_time is not None:
            start_time = '-inf'
            _b_klines = self.redisc.zrevrangebyscore(get_kline_key_name(interval, symbol), end_time, start_time,
                                                     start=0, num=limit)
            _b_klines.reverse()
        elif start_time is not None and end_time is None:
            end_time = '+inf'
            _b_klines = self.redisc.zrangebyscore(get_kline_key_name(interval, symbol), end_time, start_time,
                                                  start=0, num=limit)
        elif start_time is not None and end_time is not None:
            _b_klines = self.redisc.zrangebyscore(get_kline_key_name(interval, symbol), end_time, start_time,
                                                  start=0, num=limit)
        _klines = [json.loads(str(_b_kline, encoding='utf-8')) for _b_kline in _b_klines]
        return _klines

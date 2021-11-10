# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################
import json
from redis import StrictRedis

from KlineUtils import get_kline_key_name
from getaway.binance_http import BinanceFutureHttp


class RedisWrapperBinanceFutureHttp(BinanceFutureHttp):

    def __init__(self, timezone, redisc: StrictRedis, namespace: str = 'kline', key=None, secret=None, host=None,
                 time_adjust: bool = True, timeout=30):
        super().__init__(timezone, key=key, secret=secret, host=host, time_adjust=time_adjust, timeout=timeout)
        self.redisc = redisc
        self.namespace = namespace

    def get_kline_interval(self, symbol, interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        _b_klines = []
        if start_time is None and end_time is None:
            start_time = '-inf'
            end_time = '+inf'
            _b_klines = self.redisc.zrevrangebyscore(get_kline_key_name(self.namespace, interval, symbol), end_time, start_time,
                                                     start=0, num=limit)
            _b_klines.reverse()
        elif start_time is None and end_time is not None:
            start_time = '-inf'
            _b_klines = self.redisc.zrevrangebyscore(get_kline_key_name(self.namespace, interval, symbol), end_time, start_time,
                                                     start=0, num=limit)
            _b_klines.reverse()
        elif start_time is not None and end_time is None:
            end_time = '+inf'
            _b_klines = self.redisc.zrangebyscore(get_kline_key_name(self.namespace, interval, symbol), end_time, start_time,
                                                  start=0, num=limit)
        elif start_time is not None and end_time is not None:
            _b_klines = self.redisc.zrangebyscore(get_kline_key_name(self.namespace, interval, symbol), end_time, start_time,
                                                  start=0, num=limit)
        _klines = [json.loads(str(_b_kline, encoding='utf-8')) for _b_kline in _b_klines]
        return _klines

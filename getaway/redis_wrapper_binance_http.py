# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

from redis import StrictRedis

from KlinePush import get_kline_key_name, timestamp, interval_millseconds_map
from getaway.binance_http import BinanceFutureHttp


class RedisWrapperBinanceFutureHttp(BinanceFutureHttp):

    def __init__(self, redisc: StrictRedis, key=None, secret=None, host=None, timeout=30):
        super().__init__(key, secret, host, timeout)
        self.redisc = redisc

    def get_kline_interval(self, symbol, interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        select_limit = limit + 1
        if end_time is None:
            now = timestamp()
            end_time = now
        if start_time is None:
            interval_millseconds = interval_millseconds_map[interval]
            start_time = end_time - (interval_millseconds * select_limit)

        _klines = self.redisc.zrangebyscore(get_kline_key_name(interval, symbol), start_time, end_time,
                                            start=0, num=select_limit)
        if len(_klines) > limit:
            _klines = _klines[-limit:]
        return _klines






# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

from redis import StrictRedis

from getaway.binance_http import BinanceFutureHttp


class RedisWrapperBinanceFutureHttp(BinanceFutureHttp):

    kline_redis_namespace = 'mrmv:kline'

    def __init__(self, redisc: StrictRedis, key=None, secret=None, host=None, timeout=30):
        super().__init__(key, secret, host, timeout)
        self.redisc = redisc

    def get_kline_interval(self, symbol, interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        return self.redisc.zrangebyscore(self.get_key_name(interval, symbol), start_time, end_time, num=limit)

    def get_key_name(self, interval: str, symbol: str):
        return str.join(':', [self.kline_redis_namespace, interval, symbol])


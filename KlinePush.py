from typing import List

from config import redisc
from apscheduler.schedulers.background import BlockingScheduler

from getaway.binance_http import BinanceFutureHttp

invoker = BinanceFutureHttp()


def init_redis(bar_count: int = 99):
    exchange_info = invoker.exchangeInfo()
    symbol_infos = exchange_info['symbols']
    symbols = [symbol_info['symbol'] for symbol_info in symbol_infos]

    init_redis0('1m', symbols, bar_count)
    init_redis0('3m', symbols, bar_count)
    init_redis0('5m', symbols, bar_count)
    init_redis0('15m', symbols, bar_count)
    init_redis0('30m', symbols, bar_count)
    init_redis0('1h', symbols, bar_count)
    init_redis0('2h', symbols, bar_count)
    init_redis0('4h', symbols, bar_count)


def init_redis0(interval: str, symbols: List[str], bar_count: int = 99):
    for symbol in symbols:
        data = invoker.get_kline_interval('BTCUSDT', interval, limit=bar_count)


if __name__ == '__main__':
    init_redis()
    scheduler = BlockingScheduler()
    scheduler.start()

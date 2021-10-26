# -*- coding: utf-8 -*-
import json
import time
from typing import List

from config import redisc, timezone, clean_redis_klines, redis_klines_save_days, redis_klines_web_fetch_worker
from apscheduler.schedulers.background import BlockingScheduler
from concurrent.futures.thread import ThreadPoolExecutor

from getaway.binance_http import BinanceFutureHttp

interval_millseconds_map = {
    '1m': 1000 * 60 * 1,
    '3m': 1000 * 60 * 3,
    '5m': 1000 * 60 * 5,
    '15m': 1000 * 60 * 15,
    '30m': 1000 * 60 * 30,
    '1h': 1000 * 60 * 60 * 1,
    '2h': 1000 * 60 * 60 * 2,
    '4h': 1000 * 60 * 60 * 4,
}
fetch_order = ['4h', '2h', '1h', '30m', '15m', '5m', '3m', '1m']

last_interval_time = {}

max_workers = redis_klines_web_fetch_worker
kline_redis_namespace = 'mrmv:kline'
save_seconds = 60 * 60 * 24 * 30

scheduler = BlockingScheduler(timezone=timezone)

invoker = BinanceFutureHttp()

exchange_info = invoker.exchangeInfo()
symbol_infos = exchange_info['symbols']
symbols = [symbol_info['symbol'] for symbol_info in symbol_infos]


def get_kline_key_name(interval: str, symbol: str):
    return str.join(':', [kline_redis_namespace, interval, symbol])


def fetch_klines_loop(bar_count: int = 99):
    now = timestamp()
    for interval in fetch_order:
        period_millseconds = interval_millseconds_map[interval]
        if last_interval_time[interval] + period_millseconds <= now:
            save_klines(interval, symbols, bar_count)


def init_redis(bar_count: int = 99):
    print('redis initing...')
    for interval in fetch_order:
        save_klines(interval, symbols, bar_count)
    print('redis inited.')


def get_and_save_klines(symbol: str, interval: str, bar_count: int):
    klines = invoker.get_kline_interval(symbol, interval, limit=bar_count)
    last_kline_time = klines[-1][0]
    last_interval_time[interval] = last_kline_time

    key = get_kline_key_name(interval, symbol)
    kline_score_mapping = {json.dumps(kline): kline[0] for kline in klines}

    with redisc.pipeline(transaction=True) as pipeline:
        pipeline.zremrangebyscore(key, min(kline_score_mapping.values()), max(kline_score_mapping.values()))
        pipeline.zadd(key, kline_score_mapping)
        pipeline.execute()

    print(f'save {bar_count} klines success, symbol: {symbol}, interval: {interval}')


def save_klines(interval: str, symbols: List[str], bar_count: int = 99):
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as tp:
        for symbol in symbols:
            future = tp.submit(get_and_save_klines, symbol, interval, bar_count)
            futures.append(future)
    [future.result() for future in futures]


def clean_redis(interval: str, save_days: int):
    for symbol in symbols:
        key = get_kline_key_name(interval, symbol)
        redisc.zremrangebyscore(key, 0, timestamp() - (save_days * 1000 * 60 * 60 * 24))


def register_clean_redis_jobs(save_days: int):
    scheduler.add_job(clean_redis, id='clean_redis_4h', args=('4h', save_days), trigger='cron', hour='*/4')
    scheduler.add_job(clean_redis, id='clean_redis_2h', args=('2h', save_days), trigger='cron', hour='*/2')
    scheduler.add_job(clean_redis, id='clean_redis_1h', args=('1h', save_days), trigger='cron', hour='*')
    scheduler.add_job(clean_redis, id='clean_redis_30m', args=('30m', save_days), trigger='cron', minute='*/30')
    scheduler.add_job(clean_redis, id='clean_redis_15m', args=('15m', save_days), trigger='cron', minute='*/15')
    scheduler.add_job(clean_redis, id='clean_redis_5m', args=('5m', save_days), trigger='cron', minute='*/5')
    scheduler.add_job(clean_redis, id='clean_redis_3m', args=('3m', save_days), trigger='cron', minute='*/3')
    scheduler.add_job(clean_redis, id='clean_redis_1m', args=('1m', save_days), trigger='cron', minute='*')


def register_get_klines_loop_jobs():
    scheduler.add_job(fetch_klines_loop, id='get_klines_loop', trigger='cron', second='2')


def timestamp():
    return int(time.time() * 1000)


if __name__ == '__main__':
    init_redis()
    register_get_klines_loop_jobs()
    if clean_redis_klines:
        register_clean_redis_jobs(redis_klines_save_days)
    scheduler.start()

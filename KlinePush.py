# -*- coding: utf-8 -*-
import _thread
import json
import time
from collections import defaultdict
from typing import List, Dict

from KlineFetchWebSocketSubscriber import KlineFetchWebSocketSubscriber
from KlineUtils import symbols, invoker, get_kline_key_name
from config import redisc, timezone, clean_redis_klines, redis_klines_save_days, redis_klines_web_fetch_worker
from apscheduler.schedulers.background import BlockingScheduler
from concurrent.futures.thread import ThreadPoolExecutor

max_workers = redis_klines_web_fetch_worker
scheduler = BlockingScheduler(timezone=timezone)

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
fetch_order = [
    '4h',
    '2h',
    '1h',
    '30m',
    '15m',
    '5m',
    '3m',
    '1m'
]

last_interval_time = {}

ws_url = 'wss://fstream.binance.com/ws'
channel_count_per_ws = 100


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
        start_time = min(kline_score_mapping.values())
        end_time = max(kline_score_mapping.values())
        pipeline.zremrangebyscore(key, start_time, end_time)
        print(f'redis zremrangebyscore, key: {key}, start_time: {start_time}, end_time: {end_time}')
        pipeline.zadd(key, kline_score_mapping)
        print(f'redis zadd, key: {key}, start_time: {start_time}, end_time: {end_time}')
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
    now = timestamp()
    with redisc.pipeline(transaction=False) as pipeline:
        for symbol in symbols:
            key = get_kline_key_name(interval, symbol)
            pipeline.zremrangebyscore(key, 0, now - (save_days * 1000 * 60 * 60 * 24))
        pipeline.execute()


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


def start_stream_update():
    interval_symbols_maps = []
    current_map = defaultdict(list)
    map_channel_count = 0
    for interval in interval_millseconds_map.keys():
        for symbol in symbols:
            if map_channel_count >= channel_count_per_ws:
                current_map = defaultdict(list)
                interval_symbols_maps.append(current_map)
                map_channel_count = 0
            current_map[interval].append(symbol)
            map_channel_count = map_channel_count + 1
    interval_symbols_maps.append(current_map)

    subscribers = []
    for interval_symbols_map in interval_symbols_maps:
        subscriber = KlineFetchWebSocketSubscriber(ws_url, redisc, interval_symbols_map,
                                                   on_restart=_stream_update_restart)
        subscribers.append(subscriber)
    for subscriber in subscribers:
        _thread.start_new_thread(subscriber.start, ())


def _stream_update_restart(interval_symbols_map: Dict[str, List[str]]):
    for interval, symbols in interval_symbols_map.items():
        save_klines(interval, symbols)


def timestamp():
    return int(time.time() * 1000)


if __name__ == '__main__':
    init_redis()
    start_stream_update()
    if clean_redis_klines:
        register_clean_redis_jobs(redis_klines_save_days)
    scheduler.start()

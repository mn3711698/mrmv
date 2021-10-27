# -*- coding: utf-8 -*-
import _thread
import json
import time
from collections import defaultdict
from typing import List

from KlineFetchWebSocketSubscriber import KlineFetchWebSocketSubscriber, SubscriberSymbolsBody
from KlineUtils import symbols, invoker, get_kline_key_name, interval_millseconds_map, timestamp
from config import redisc, timezone, clean_redis_klines, redis_klines_save_days, redis_klines_web_fetch_worker
from apscheduler.schedulers.background import BlockingScheduler
from concurrent.futures.thread import ThreadPoolExecutor

max_workers = redis_klines_web_fetch_worker
scheduler = BlockingScheduler(timezone=timezone)

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

save_klines_thread_pool = ThreadPoolExecutor(max_workers=max_workers)

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
        pipeline.zadd(key, kline_score_mapping)
        pipeline.execute()

    print(f'save {bar_count} klines success, symbol: {symbol}, interval: {interval}')


def save_klines(interval: str, symbols: List[str], bar_count: int = 99):
    futures = []
    for symbol in symbols:
        future = save_klines_thread_pool.submit(get_and_save_klines, symbol, interval, bar_count)
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
        for symbol in ['1000SHIBUSDT']:
        # for symbol in symbols:
            if map_channel_count >= channel_count_per_ws:
                interval_symbols_maps.append(current_map)
                current_map = defaultdict(list)
                map_channel_count = 0
            current_map[interval].append(symbol)
            map_channel_count = map_channel_count + 1
    interval_symbols_maps.append(current_map)

    subscribers = []
    for interval_symbols_map in interval_symbols_maps:
        symbols_body = SubscriberSymbolsBody(interval_symbols_map)
        subscriber = KlineFetchWebSocketSubscriber(ws_url, redisc, symbols_body,
                                                   with_start=_stream_update_with_start, save_buffer_millseconds=-1)
        subscribers.append(subscriber)
    for subscriber in subscribers:
        _thread.start_new_thread(subscriber.start, ())


def _stream_update_with_start(symbols_body: SubscriberSymbolsBody):
    for interval, symbols in symbols_body.interval_symbols_map.items():
        save_klines(interval, symbols)


if __name__ == '__main__':
    # init_redis()
    start_stream_update()
    if clean_redis_klines:
        register_clean_redis_jobs(redis_klines_save_days)
    scheduler.start()

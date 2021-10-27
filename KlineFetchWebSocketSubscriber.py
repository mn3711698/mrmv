import _thread
import json
from typing import List, Dict

from websocket import WebSocketApp
from redis import StrictRedis

import config
from KlineUtils import get_kline_key_name


class KlineFetchWebSocketSubscriber(object):
    def __init__(self, host: str, redisc: StrictRedis, interval_symbols_map: Dict[str, List[str]], with_start=None):
        self._ws = WebSocketApp(host, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error,
                                on_message=self._on_message)
        self.with_start = with_start
        self._interval_symbols_map = interval_symbols_map
        self._redisc = redisc
        self._subscribe_params = []
        for interval, symbols in interval_symbols_map.items():
            for symbol in symbols:
                subscribe_key = f'{symbol.lower()}@kline_{interval}'
                self._subscribe_params.append(subscribe_key)

    def start(self):
        if self.with_start is not None:
            _thread.start_new_thread(self.with_start, [self._interval_symbols_map])
        self._ws.run_forever(ping_interval=15)

    def _restart(self):
        self.start()

    def _on_open(self, ws: WebSocketApp):
        print(f'websocket connection opened, klines: {self._subscribe_params} subscribing...')
        subscribe_data = {
            "method": "SUBSCRIBE",
            "params": self._subscribe_params,
            "id": 1
        }
        ws.send(json.dumps(subscribe_data))
        print(f'klines: {self._subscribe_params} subscribe success.')

    def _on_close(self, ws: WebSocketApp):
        print(f'subscriber: {self._subscribe_params} closed.')

    def _on_error(self, ws: WebSocketApp, error):
        print(f'subscriber: {self._subscribe_params} error occured: {error}, restart.')
        ws.close()
        self._restart()

    def _on_message(self, ws: WebSocketApp, message):
        try:
            body = None
            if type(message) is str:
                body = json.loads(message)
            if type(body) is not dict:
                return
        except Exception as e:
            print(f'message: {message} load failed: {e}, return')
            return
        if 'e' not in body or 'kline' != body['e']:
            return
        symbol = body['s']
        kline_time = body['E']
        kline_info = body['k']
        kline_start_time = kline_info['t']
        kline_end_time = min(int(kline_time), kline_info['T'])
        interval = kline_info['i']
        key = get_kline_key_name(interval, symbol)

        kline = [
          kline_start_time,   # kline start time
          kline_info['o'],    # kline open price
          kline_info['h'],    # kline high price
          kline_info['l'],    # kline low price
          kline_info['c'],    # kline close price
          kline_info['v'],    # kline volume
          kline_end_time,     # kline end time
          kline_info['q'],    # kline deal amount
          kline_info['n'],    # kline deal count
          kline_info['V'],    # kline positive deal count
          kline_info['Q'],    # kline positive deal amount
          "0"
        ]

        insert_new_kline = True
        remove_old_kline = False
        compare_klines = self._redisc.zrangebyscore(key, kline_start_time, kline_start_time)
        if len(compare_klines) > 0:
            compare_kline = compare_klines[0]
            compare_kline_end_time = compare_kline[6]
            if int(compare_kline_end_time) < int(kline[6]):
                remove_old_kline = True
            else:
                insert_new_kline = False
        with self._redisc.pipeline(transaction=True) as pipeline:
            if remove_old_kline:
                pipeline.zremrangebyscore(key, kline_start_time, kline_time)
            if insert_new_kline:
                pipeline.zadd(key, {json.dumps(kline): kline_start_time})
            pipeline.execute()
        print(f'{symbol}/{interval} kline: {kline} updated.')


if __name__ == '__main__':
    interval_symbols_map = {
        '1m': ['BTCUSDT', 'ETHUSDT'],
        '5m': ['EOSUSDT', 'SXPUSDT']
    }
    ws_url = 'wss://fstream.binance.com/ws'
    subscriber = KlineFetchWebSocketSubscriber(ws_url, config.redisc, interval_symbols_map)
    subscriber.start()

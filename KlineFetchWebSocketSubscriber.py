import _thread
import json
from collections import defaultdict
from threading import Lock
from typing import List, Dict

from websocket import WebSocketApp
from redis import StrictRedis

from KlineUtils import get_kline_key_name, timestamp


class SubscriberSymbolsBody(object):
    def __init__(self, interval_symbols_map: Dict[str, List[str]]):
        self.interval_symbols_map = interval_symbols_map


class KlineBuffer(object):
    def __init__(self, kline):
        self.lock = Lock()
        self.kline = kline
        self.last_save_time = None


class KlineFetchWebSocketSubscriber(object):
    interval_symbol_kline_buffer_map: Dict[str, Dict[str, KlineBuffer]] = defaultdict(dict)

    def __init__(self, host: str, redisc: StrictRedis, symbols_body: SubscriberSymbolsBody,
                 with_start=None, save_buffer_millseconds: int = 1000 * 10):
        self.host = host
        self._ws = WebSocketApp(self.host, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error,
                                on_message=self._on_message)
        self.with_start = with_start
        self.save_buffer_millseconds = save_buffer_millseconds
        self._symbols_body = symbols_body
        self._interval_symbols_map = self._symbols_body.interval_symbols_map
        self._redisc = redisc
        self._subscribe_params = []
        for interval, symbols in self._interval_symbols_map.items():
            for symbol in symbols:
                subscribe_key = f'{symbol.lower()}@kline_{interval}'
                self._subscribe_params.append(subscribe_key)
                self.interval_symbol_kline_buffer_map[interval][symbol] = KlineBuffer(None)

    def start(self):
        if self.with_start is not None:
            _thread.start_new_thread(self.with_start, (self._symbols_body,))
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
        self._ws = WebSocketApp(self.host, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error,
                                on_message=self._on_message)
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
          "0",
          kline_time
        ]

        save_kline = kline
        if self.save_buffer_millseconds is not None and self.save_buffer_millseconds > 0:
            kline_buffer = self.interval_symbol_kline_buffer_map[interval][symbol]
            is_save_kline = False
            now = timestamp()
            with kline_buffer.lock:
                if kline_buffer.kline is None:
                    kline_buffer.kline = kline
                else:
                    if kline[0] > kline_buffer.kline[6]:
                        is_save_kline = True
                    if kline_buffer.last_save_time is None \
                            or kline_buffer.last_save_time + self.save_buffer_millseconds < now:
                        is_save_kline = True
                if is_save_kline:
                    save_kline = kline_buffer.kline
                    kline_buffer.kline = kline
                    kline_buffer.last_save_time = now
                else:
                    if kline[0] == kline_buffer.kline[0] and kline[-1] > kline_buffer.kline[-1]:
                        kline_buffer.kline = kline
            if not is_save_kline:
                return

        # save_kline = save_kline[:-1]
        insert_new_kline = True
        remove_old_kline = False
        compare_klines = self._redisc.zrangebyscore(key, save_kline[0], save_kline[0])
        if len(compare_klines) > 0:
            compare_kline = compare_klines[0]
            compare_kline_end_time = compare_kline[6]
            if int(compare_kline_end_time) < int(save_kline[6]):
                remove_old_kline = True
            else:
                insert_new_kline = False
        with self._redisc.pipeline(transaction=True) as pipeline:
            if remove_old_kline:
                pipeline.zremrangebyscore(key, save_kline[0], save_kline[-1])
            if insert_new_kline:
                # this kline include a last value(event time), sep it to normalize
                pipeline.zadd(key, {json.dumps(save_kline[:-1]): save_kline[0]})
            pipeline.execute()
        print(f'{symbol}/{interval} kline: {save_kline} updated.')

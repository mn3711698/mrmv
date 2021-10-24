# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import json
from datetime import datetime
from getaway.base_websocket import BaseWebsocket
from utils.event.engine import EventEngine, Event
from constant.constant import EVENT_TICKER, EVENT_DEPTH


class BinanceDataWebsocket(BaseWebsocket):
    def __init__(self, broker=None, ping_interval=20):

        self.broker = broker
        host = "wss://fstream.binance.com/stream?streams="
        super(BinanceDataWebsocket, self).__init__(host=host, ping_interval=ping_interval)
        self.symbols = set()

    def on_msg(self, data: str):
        json_msg = json.loads(data)
        stream = json_msg["stream"]
        symbol, channel = stream.split("@")
        data = json_msg["data"]
        if channel == 'ticker':
            if self.broker:
                engine: EventEngine = self.broker.event_engine
                ticker = {"volume": float(data['v']),
                          "open_price": float(data['o']),
                          "high_price": float(data['h']),
                          "low_price": float(data['l']),
                          "last_price": float(data['c']),
                          "datetime": data['E'],
                          "symbol": symbol.upper()
                        }
                event = Event(EVENT_TICKER, {"ticker": ticker})
                engine.put(event)

        elif channel == 'depth5':
            if self.broker:
                engine: EventEngine = self.broker.event_engine
                depth = {
                        "last_ask": float(data['a'][0][0]),
                        "ask2": float(data['a'][1][0]),
                        "ask3": float(data['a'][2][0]),
                        "last_bid": float(data['b'][0][0]),
                        "bid2": float(data['b'][1][0]),
                        "bid3": float(data['b'][2][0]),
                        "datetime": datetime.fromtimestamp(float(data['E']) / 1000),
                        "symbol": symbol.upper()
                        }

                event = Event(EVENT_DEPTH, {"depth": depth})
                engine.put(event)

        else:
            print(channel, data)

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        print("on error")

    def subscribe(self, symbols):

        if isinstance(symbols, list):
            for i in symbols:
                self.symbols.add(i)
        else:
            self.symbols.add(symbols)
        if self._active:
            self.stop()
            self.join()
        channels = []
        for symbol in self.symbols:
            channels.append(symbol.lower()+"@ticker")
            channels.append(symbol.lower() + "@depth5")

        self.host += '/'.join(channels)
        self.start()


class BinanceSpotWebsocket(BaseWebsocket):

    def __init__(self, broker=None, ping_interval=20):

        self.broker = broker
        host = "wss://fstream.binance.com:9443/stream?streams="
        super(BinanceSpotWebsocket, self).__init__(host=host, ping_interval=ping_interval)
        self.symbols = set()

    def on_msg(self, data: str):
        json_msg = json.loads(data)
        stream = json_msg["stream"]
        symbol, channel = stream.split("@")
        data = json_msg["data"]
        if channel == 'ticker':
            if self.broker:
                engine: EventEngine = self.broker.event_engine
                ticker = {"volume": float(data['v']),
                          "open_price": float(data['o']),
                          "high_price": float(data['h']),
                          "low_price": float(data['l']),
                          "last_price": float(data['c']),
                          "datetime": data['E'],
                          "symbol": symbol.upper()
                        }
                event = Event(EVENT_TICKER, {"ticker": ticker})
                engine.put(event)

        else:
            print(channel, data)

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        print("on error")

    def subscribe(self, symbol):
        if isinstance(symbol, list):
            for i in symbol:
                self.symbols.add(i)
        else:
            self.symbols.add(symbol)
        if self._active:
            self.stop()
            self.join()
        channels = []
        for symbol in self.symbols:
            channels.append(symbol.lower()+"@ticker")
            # channels.append(symbol.lower() + "@depth5")

        self.host += '/'.join(channels)
        self.start()


if __name__ == '__main__':
    ws = BinanceDataWebsocket()
    ws.subscribe('bnbusdt')


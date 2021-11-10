
from utils.event.engine import EventEngine
from getaway.binance_http import BinanceFutureHttp
from getaway.binance_ws import BinanceDataWebsocket


class Broker(object):

    def __init__(self, timezone, engine: EventEngine, binance_http=None, key=None, secret=None, symbols_list=None):
        self.event_engine = engine

        if binance_http is None:
            self.binance_http = BinanceFutureHttp(timezone, key=key, secret=secret)
        else:
            self.binance_http = binance_http

        self.binance_data_ws = BinanceDataWebsocket(broker=self)
        self.binance_data_ws.subscribe(symbols_list)
        self.event_engine.start()
        self.strategies_dict = {}

    def add_strategy(self, strategy_class, symbols_dict, min_volume_dict, trading_size_dict):
        self.strategies_dict[strategy_class.__name__] = strategy_class(self, symbols_dict, min_volume_dict,
                                                                       trading_size_dict)


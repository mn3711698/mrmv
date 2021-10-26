from getaway.binance_http import BinanceFutureHttp


kline_redis_namespace = 'mrmv:kline'

invoker = BinanceFutureHttp()

exchange_info = invoker.exchangeInfo()
symbol_infos = exchange_info['symbols']
symbols = [symbol_info['symbol'] for symbol_info in symbol_infos]


def get_kline_key_name(interval: str, symbol: str):
    return str.join(':', [kline_redis_namespace, interval, symbol])
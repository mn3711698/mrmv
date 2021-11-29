# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################

import requests
import time
import hmac
import hashlib
from enum import Enum
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler


class OrderStatus(object):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"


class RequestMethod(Enum):
    """
    请求的方法.
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class Interval(Enum):
    """
    请求的K线数据..
    """
    MINUTE_1 = '1m'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1d'
    DAY_3 = '3d'
    WEEK_1 = '1w'
    MONTH_1 = '1M'


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BinanceFutureHttp(object):

    def __init__(self, timezone, key=None, secret=None, host=None, time_adjust: bool = False, timeout=30):
        self.key = key
        self.secret = secret
        self.host = host if host else "https://fapi.binance.com"
        self.recv_window = 5000
        self.timeout = timeout
        self.order_count_lock = Lock()
        self.order_count = 1_000_000
        self.time_offset = 0
        if time_adjust:
            self.time_offset_scheduler = BackgroundScheduler(timezone=timezone)
            self.time_offset_scheduler.add_job(self.tune_time_offset, trigger='cron', id='time_offset_update',
                                               minute='*')
            self.time_offset_scheduler.start()

    def tune_time_offset(self):
        server_time = self.server_time()['serverTime']
        sys_time = int(time.time() * 1000)
        self.time_offset = sys_time - server_time

    def build_parameters(self, params: dict):
        keys = list(params.keys())
        keys.sort()
        return '&'.join([f"{key}={params[key]}" for key in params.keys()])

    def request(self, req_method: RequestMethod, path: str, requery_dict=None, verify=False):
        url = self.host + path

        if verify:
            query_str = self._sign(requery_dict)
            url += '?' + query_str
        elif requery_dict:
            url += '?' + self.build_parameters(requery_dict)
        headers = {"X-MBX-APIKEY": self.key}
        return requests.request(req_method.value, url=url, headers=headers, timeout=self.timeout).json()

    def response(self, req_method: RequestMethod, path: str, requery_dict=None, verify=False):
        url = self.host + path

        if verify:
            query_str = self._sign(requery_dict)
            url += '?' + query_str
        elif requery_dict:
            url += '?' + self.build_parameters(requery_dict)
        headers = {"X-MBX-APIKEY": self.key}
        return requests.request(req_method.value, url=url, headers=headers, timeout=self.timeout)

    def bbkline_request(self, req_method: RequestMethod, path: str, requery_dict=None, verify=False):
        url = "https://api.binance.com" + path

        if verify:
            query_str = self._sign(requery_dict)
            url += '?' + query_str
        elif requery_dict:
            url += '?' + self.build_parameters(requery_dict)
        headers = {"X-MBX-APIKEY": self.key}
        return requests.request(req_method.value, url=url, headers=headers, timeout=self.timeout).json()

    def server_time(self):
        path = '/fapi/v1/time'
        return self.request(req_method=RequestMethod.GET, path=path)

    def exchangeInfo(self):

        """
        {'timezone': 'UTC', 'serverTime': 1570802268092, 'rateLimits':
        [{'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 1200},
        {'rateLimitType': 'ORDERS', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 1200}],
         'exchangeFilters': [], 'symbols':
         [{'symbol': 'BTCUSDT', 'status': 'TRADING', 'maintMarginPercent': '2.5000', 'requiredMarginPercent': '5.0000',
         'baseAsset': 'BTC', 'quoteAsset': 'USDT', 'pricePrecision': 2, 'quantityPrecision': 3, 'baseAssetPrecision': 8,
         'quotePrecision': 8,
         'filters': [{'minPrice': '0.01', 'maxPrice': '100000', 'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
         {'stepSize': '0.001', 'filterType': 'LOT_SIZE', 'maxQty': '1000', 'minQty': '0.001'},
         {'stepSize': '0.001', 'filterType': 'MARKET_LOT_SIZE', 'maxQty': '1000', 'minQty': '0.001'},
         {'limit': 200, 'filterType': 'MAX_NUM_ORDERS'},
         {'multiplierDown': '0.8500', 'multiplierUp': '1.1500', 'multiplierDecimal': '4', 'filterType': 'PERCENT_PRICE'}],
         'orderTypes': ['LIMIT', 'MARKET', 'STOP'], 'timeInForce': ['GTC', 'IOC', 'FOK', 'GTX']}]}

        :return:
        """

        path = '/fapi/v1/exchangeInfo'
        return self.request(req_method=RequestMethod.GET, path=path)

    def order_book(self, symbol, limit=5):
        limits = [5, 10, 20, 50, 100, 500, 1000]
        if limit not in limits:
            limit = 5

        path = "/fapi/v1/depth"
        query_dict = {"symbol": symbol,
                      "limit": limit
                      }
        return self.request(RequestMethod.GET, path, query_dict)

    def get_kline(self, symbol, interval: Interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        """
        :param symbol:
        :param interval:
        :param start_time:
        :param end_time:
        :param limit:
        :return:
        [
            1499040000000,      // 开盘时间
            "0.01634790",       // 开盘价
            "0.80000000",       // 最高价
            "0.01575800",       // 最低价
            "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
            "148976.11427815",  // 成交量
            1499644799999,      // 收盘时间
            "2434.19055334",    // 成交额
            308,                // 成交笔数
            "1756.87402397",    // 主动买入成交量
            "28.46694368",      // 主动买入成交额
            "17928899.62484339" // 请忽略该参数
        ]
        """
        path = "/fapi/v1/klines"
        query_dict = {
            "symbol": symbol,
            "interval": interval.value,
            "limit": limit
        }

        if start_time:
            query_dict['startTime'] = start_time

        if end_time:
            query_dict['endTime'] = end_time
        data = ''
        for i in range(max_try_time):
            mdata = self.request(RequestMethod.GET, path, query_dict)
            if isinstance(mdata, list) and len(mdata):
                return mdata
            return data

    def get_kline_interval(self, symbol, interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        """
        :param symbol:
        :param interval:
        :param start_time:
        :param end_time:
        :param limit:
        :return:
        [
            1499040000000,      // 开盘时间
            "0.01634790",       // 开盘价
            "0.80000000",       // 最高价
            "0.01575800",       // 最低价
            "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
            "148976.11427815",  // 成交量
            1499644799999,      // 收盘时间
            "2434.19055334",    // 成交额
            308,                // 成交笔数
            "1756.87402397",    // 主动买入成交量
            "28.46694368",      // 主动买入成交额
            "17928899.62484339" // 请忽略该参数
        ]
        """
        path = "/fapi/v1/klines"
        query_dict = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        if start_time:
            query_dict['startTime'] = start_time

        if end_time:
            query_dict['endTime'] = end_time
        data = ''
        for i in range(max_try_time):
            mdata = self.request(RequestMethod.GET, path, query_dict)
            if isinstance(mdata, list) and len(mdata):
                return mdata
            return data

    def more_get_kline(self, symbol, interval: Interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        # get_kline
        path = "/fapi/v1/klines"
        query_dict = {
            "symbol": symbol,
            "interval": interval.value,
            "limit": limit
        }

        if start_time:
            query_dict['startTime'] = start_time

        if end_time:
            query_dict['endTime'] = end_time

        res = self.response(RequestMethod.GET, path, query_dict)
        data = res.json()
        headers = res.headers
        mbx = headers.get('X-MBX-USED-WEIGHT-1M')
        if isinstance(data, list) and len(data):
            return data, mbx
        return data, mbx

    def get_bbkline(self, symbol, interval: Interval, start_time=None, end_time=None, limit=500, max_try_time=10):
        """

        :param symbol:
        :param interval:
        :param start_time:
        :param end_time:
        :param limit:
        :return:
        [
            1499040000000,      // 开盘时间
            "0.01634790",       // 开盘价
            "0.80000000",       // 最高价
            "0.01575800",       // 最低价
            "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
            "148976.11427815",  // 成交量
            1499644799999,      // 收盘时间
            "2434.19055334",    // 成交额
            308,                // 成交笔数
            "1756.87402397",    // 主动买入成交量
            "28.46694368",      // 主动买入成交额
            "17928899.62484339" // 请忽略该参数
        ]
        """
        # path = "/fapi/v1/klines"
        path = "/api/v1/klines"
        query_dict = {
            "symbol": symbol,
            "interval": interval.value,
            "limit": limit
        }

        if start_time:
            query_dict['startTime'] = start_time

        if end_time:
            query_dict['endTime'] = end_time

        for i in range(max_try_time):
            data = self.bbkline_request(RequestMethod.GET, path, query_dict)
            if isinstance(data, list) and len(data):
                return data

    def get_latest_price(self, symbol):
        path = "/fapi/v1/ticker/price"
        query_dict = {"symbol": symbol}
        return self.request(RequestMethod.GET, path, query_dict)

    def get_ticker(self, symbol):
        path = "/fapi/v1/ticker/bookTicker"
        query_dict = {"symbol": symbol}
        return self.request(RequestMethod.GET, path, query_dict)

    def _new_order_id(self):
        """
        生成一个order_id..
        :return:
        """
        with self.order_count_lock:
            self.order_count += 1
            return self.order_count

    def _timestamp(self):
        return int(time.time() * 1000) - self.time_offset

    def _sign(self, params):

        requery_string = self.build_parameters(params)
        hexdigest = hmac.new(self.secret.encode('utf8'), requery_string.encode("utf-8"), hashlib.sha256).hexdigest()
        return requery_string + '&signature=' + str(hexdigest)

    def order_id(self):
        return str(self._timestamp() + self._new_order_id())

    def place_order(self, symbol: str, side: OrderSide, order_type: OrderType, quantity, price,
                    client_prefix=None, time_inforce="GTC", recvWindow=5000, stop_price=0):

        """
        下单..
        :param symbol: BTCUSDT
        :param side: BUY or SELL
        :param type: LIMIT MARKET STOP
        :param quantity: 数量.
        :param price: 价格
        :param stop_price: 停止单的价格.
        :param time_inforce:
        :param params: 其他参数

        LIMIT : timeInForce, quantity, price
        MARKET : quantity
        STOP: quantity, price, stopPrice
        :return:

        """

        path = '/fapi/v1/order'

        params = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": quantity,
            "price": price,
            "recvWindow": recvWindow,
            "timestamp": self._timestamp()
        }

        if order_type == OrderType.LIMIT:
            params['timeInForce'] = time_inforce

        if order_type == OrderType.MARKET:
            if params.get('price'):
                del params['price']

        if order_type == OrderType.STOP:
            if stop_price > 0:
                params["stopPrice"] = stop_price
            else:
                raise ValueError("stopPrice must greater than 0")
        return self.request(RequestMethod.POST, path=path, requery_dict=params, verify=True)

    def BOTHplace_order(self, symbol: str, side: OrderSide, positionSide: PositionSide, order_type: OrderType,
                        quantity, price, client_prefix=None, time_inforce="GTC", recvWindow=5000, stop_price=0):

        """
        双向持仓下单..
        :param symbol: BTCUSDT
        :param side: BUY or SELL
        :param type: LIMIT MARKET STOP
        :param quantity: 数量.
        :param price: 价格
        :param stop_price: 停止单的价格.
        :param time_inforce:
        :param params: 其他参数

        LIMIT : timeInForce, quantity, price
        MARKET : quantity
        STOP: quantity, price, stopPrice
        :return:

        """

        path = '/fapi/v1/order'

        params = {
            "symbol": symbol,
            "side": side.value,
            "positionSide": positionSide.value,
            "type": order_type.value,
            "quantity": quantity,
            "price": price,
            "recvWindow": recvWindow,
            "timestamp": self._timestamp()
        }

        if order_type == OrderType.LIMIT:
            params['timeInForce'] = time_inforce

        if order_type.value == 'MARKET' or order_type == OrderType.MARKET:
            if params.get('price'):
                del params['price']

        if order_type == OrderType.STOP:
            if stop_price > 0:
                params["stopPrice"] = stop_price
            else:
                raise ValueError("stopPrice must greater than 0")
        # print(params)
        return self.request(RequestMethod.POST, path=path, requery_dict=params, verify=True)

    def get_order(self,symbol, order_id=None):
        path = "/fapi/v1/order"
        query_dict = {"symbol": symbol, "timestamp": self._timestamp()}
        if order_id:
            query_dict["orderId"] = order_id

        return self.request(RequestMethod.GET, path, query_dict, verify=True)

    def cancel_order(self, symbol, order_id=None):
        path = "/fapi/v1/order"
        params = {"symbol": symbol, "timestamp": self._timestamp()}
        if order_id:
            params["orderId"] = order_id

        return self.request(RequestMethod.DELETE, path, params, verify=True)

    def set_leverage(self, symbol: str, leverage: int):
        path = "/fapi/v1/leverage"
        params = {"symbol": symbol, "leverage": leverage, "timestamp": self._timestamp()}

        return self.request(RequestMethod.POST, path, params, verify=True)

    def get_open_orders(self, symbol=None):
        path = "/fapi/v1/openOrders"

        params = {"timestamp": self._timestamp()}
        if symbol:
            params["symbol"] = symbol

        return self.request(RequestMethod.GET, path, params, verify=True)

    def get_balance(self):
        """
        [{'accountId': 18396, 'asset': 'USDT', 'balance': '530.21334791', 'withdrawAvailable': '530.21334791', 'updateTime': 1570330854015}]
        :return:
        """
        path = "/fapi/v1/balance"
        params = {"timestamp": self._timestamp()}

        return self.request(RequestMethod.GET, path=path, requery_dict=params, verify=True)

    def get_account_info(self):
        """
        {'feeTier': 2, 'canTrade': True, 'canDeposit': True, 'canWithdraw': True, 'updateTime': 0, 'totalInitialMargin': '0.00000000',
        'totalMaintMargin': '0.00000000', 'totalWalletBalance': '530.21334791', 'totalUnrealizedProfit': '0.00000000',
        'totalMarginBalance': '530.21334791', 'totalPositionInitialMargin': '0.00000000', 'totalOpenOrderInitialMargin': '0.00000000',
        'maxWithdrawAmount': '530.2133479100000', 'assets':
        [{'asset': 'USDT', 'walletBalance': '530.21334791', 'unrealizedProfit': '0.00000000', 'marginBalance': '530.21334791',
        'maintMargin': '0.00000000', 'initialMargin': '0.00000000', 'positionInitialMargin': '0.00000000', 'openOrderInitialMargin': '0.00000000',
        'maxWithdrawAmount': '530.2133479100000'}]}
        :return:
        """
        path = "/fapi/v1/account"
        params = {"timestamp": self._timestamp()}
        return self.request(RequestMethod.GET, path, params, verify=True)

    def get_position_info(self):
        """
        [{'symbol': 'BTCUSDT', 'positionAmt': '0.000', 'entryPrice': '0.00000', 'markPrice': '8326.40833498', 'unRealizedProfit': '0.00000000', 'liquidationPrice': '0'}]
        :return:
        """
        path = "/fapi/v1/positionRisk"
        params = {"timestamp": self._timestamp()}
        return self.request(RequestMethod.GET, path, params, verify=True)

    def get_openInterestHist(self,symbol,period='5m',limit=10): #合约持仓量
        path = "/futures/data/openInterestHist"
        query_dict = {"symbol": symbol,"period":period,"limit":limit}
        return self.request(RequestMethod.GET, path, query_dict)

    def get_topLongShortAccountRatio(self,symbol,period='5m',limit=10):#大户账户数多空比
        path = "/futures/data/topLongShortAccountRatio"
        query_dict = {"symbol": symbol,"period":period,"limit":limit}
        return self.request(RequestMethod.GET, path, query_dict)

    def get_topLongShortPositionRatio(self,symbol,period='5m',limit=10):#大户持仓量多空比
        path = "/futures/data/topLongShortPositionRatio"
        query_dict = {"symbol": symbol,"period":period,"limit":limit}
        return self.request(RequestMethod.GET, path, query_dict)

    def get_globalLongShortAccountRatio(self,symbol,period='5m',limit=10):#多空持仓人数比
        path = "/futures/data/globalLongShortAccountRatio"
        query_dict = {"symbol": symbol,"period":period,"limit":limit}
        return self.request(RequestMethod.GET, path, query_dict)

    def get_takerlongshortRatio(self,symbol,period='5m',limit=10):#合约主动买卖量
        path = "/futures/data/takerlongshortRatio"
        query_dict = {"symbol": symbol,"period":period,"limit":limit}
        return self.request(RequestMethod.GET, path, query_dict)


class BinanceSpotHttp(object):

    def __init__(self, key=None, secret=None, host=None, timeout=30):
        self.key = key
        self.secret = secret
        self.host = host if host else "https://api.binance.com"
        self.recv_window = 5000
        self.timeout = timeout
        self.order_count_lock = Lock()
        self.order_count = 1_000_000

    def build_parameters(self, params: dict):
        keys = list(params.keys())
        keys.sort()
        return '&'.join([f"{key}={params[key]}" for key in params.keys()])

    def _new_order_id(self):
        """
        生成一个order_id..
        :return:
        """
        with self.order_count_lock:
            self.order_count += 1
            return self.order_count

    def _timestamp(self):
        return int(time.time() * 1000)

    def _sign(self, params):

        requery_string = self.build_parameters(params)
        hexdigest = hmac.new(self.secret.encode('utf8'), requery_string.encode("utf-8"), hashlib.sha256).hexdigest()
        return requery_string + '&signature=' + str(hexdigest)

    def request(self, req_method: RequestMethod, path: str, requery_dict=None, verify=False):
        url = self.host + path

        if verify:
            query_str = self._sign(requery_dict)
            url += '?' + query_str
        elif requery_dict:
            url += '?' + self.build_parameters(requery_dict)
        headers = {"X-MBX-APIKEY": self.key}
        return requests.request(req_method.value, url=url, headers=headers, timeout=self.timeout).json()

    def cancel_order(self, symbol, order_id=None):  # 撤销订单 (TRADE)
        path = "/api/v1/order"
        params = {"symbol": symbol, "timestamp": self._timestamp()}
        if order_id:
            params["orderId"] = order_id
        return self.request(RequestMethod.DELETE, path, params, verify=True)

    def get_open_orders(self, symbol=None):  # 当前挂单
        path = "/api/v1/openOrders"

        params = {"timestamp": self._timestamp()}
        if symbol:
            params["symbol"] = symbol

        return self.request(RequestMethod.GET, path, params, verify=True)

    def get_account_info(self):  # 账户信息 (USER_DATA)
        """
        {"makerCommission": 15,"takerCommission": 15,"buyerCommission": 0,"sellerCommission": 0,"canTrade": true,
        "canWithdraw": true,"canDeposit": true,"updateTime": 123456789,"accountType": "SPOT",
        "balances": [{"asset": "BTC","free": "4723846.89208129","locked": "0.00000000"},
        {"asset": "LTC","free": "4763368.68006011","locked": "0.00000000"}],
        "permissions": ["SPOT"]}
        """
        path = "/api/v1/account"
        params = {"timestamp": self._timestamp()}
        return self.request(RequestMethod.GET, path, params, verify=True)

    def order_id(self):
        return str(self._timestamp() + self._new_order_id())

    def place_order(self, symbol: str, side: OrderSide, order_type:OrderType, quantity, price, client_prefix=None, time_inforce="GTC", recvWindow=5000, stop_price=0):

        """
        下单..
        :param symbol: BTCUSDT
        :param side: BUY or SELL
        :param type: LIMIT MARKET STOP
        :param quantity: 数量.
        :param price: 价格
        :param stop_price: 停止单的价格.
        :param time_inforce:
        :param params: 其他参数
        LIMIT : timeInForce, quantity, price
        MARKET : quantity
        STOP: quantity, price, stopPrice
        :return:
        """
        path = '/api/v1/order'
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": quantity,
            "price": price,
            "recvWindow": recvWindow,
            "timestamp": self._timestamp()
        }

        if order_type == OrderType.LIMIT:
            params['timeInForce'] = time_inforce

        if order_type == OrderType.MARKET:
            if params.get('price'):
                del params['price']

        if order_type == OrderType.STOP:
            if stop_price > 0:
                params["stopPrice"] = stop_price
            else:
                raise ValueError("stopPrice must greater than 0")
        return self.request(RequestMethod.POST, path=path, requery_dict=params, verify=True)

    def get_order(self, symbol, order_id=None):  # 查询订单
        path = "/api/v1/order"
        query_dict = {"symbol": symbol, "timestamp": self._timestamp()}
        if order_id:
            query_dict["orderId"] = order_id
        return self.request(RequestMethod.GET, path, query_dict, verify=True)

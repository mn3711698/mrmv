# -*- coding: utf-8 -*-
##############################################################################
# Author：QQ173782910
##############################################################################

from strategies import Base


class LineWith(Base):

    def on_pos_data(self, symbol, pos_dict):
        # 先判断是否有仓位，如果是多头的仓位， 然后检查下是多头还是空头，设置相应的止损的价格..
        current_pos = float(pos_dict['positionAmt'])
        pos = self.pos_dict.get(symbol, 0)
        if pos != current_pos:  # 检查仓位是否是一一样的.
            open_orders = self.broker.binance_http.get_open_orders(symbol)
            buy_flag = 0
            sell_flag = 0
            if isinstance(open_orders, list) and len(open_orders) > 0:
                for o in open_orders:
                    if o["side"] == 'BUY':  # 开多未成交
                        buy_flag = 1
                    elif o["side"] == 'SELL':  # 平仓未成交
                        sell_flag = 1

            if current_pos == 0 and buy_flag == 0:  # 无持仓且不存在开仓单
                msg = f"仓位检查:{symbol},交易所帐户仓位为0，无持仓，系统仓位为:{pos},重置为0"
                self.dingding(msg, symbols=symbol)
                self.pos_dict[symbol] = 0
            elif current_pos != 0 and sell_flag == 0:  # 有持仓且不存在平仓单
                info = self.broker.binance_http.get_position_info()
                if isinstance(info, list):
                    for item in info:
                        symbolm = item["symbol"]
                        positionSide = item["positionSide"]
                        if symbolm == symbol and positionSide == 'BOTH':
                            current_pos = float(item['positionAmt'])
                if current_pos == 0:
                    return
                msg = f"仓位检查:{symbol},交易所仓位为:{current_pos},系统仓位为:{pos},重置为:{current_pos}"
                self.dingding(msg, symbols=symbol)
                self.pos_dict[symbol] = current_pos

        if current_pos != 0:
            unRealizedProfit = float(pos_dict['unRealizedProfit'])
            entryPrice = float(pos_dict['entryPrice'])

            if self.enter_price_dict.get(symbol, 0) == 0 or self.enter_price_dict.get(symbol, 0) != entryPrice:
                self.enter_price_dict[symbol] = entryPrice
                self.win_price_dict[symbol] = entryPrice * self.win_args_dict.get(symbol, 0)
                self.high_price_dict[symbol] = entryPrice
                self.low_price_dict[symbol] = entryPrice
                HYJ_jd_ss_dict = self.redisc.get('%s_jdss' % symbol)
                if HYJ_jd_ss_dict:
                    jd_ss = int(HYJ_jd_ss_dict.decode("utf8"))  # 1停止
                    if jd_ss == 1:
                        self.order_flag_dict[symbol] = entryPrice * self.add_args_dict.get(symbol, 0)
                    else:
                        self.order_flag_dict[symbol] = 0
                else:
                    self.order_flag_dict[symbol] = 0
            self.unRealizedProfit_dict[symbol] = unRealizedProfit
            maxunRealizedProfit = self.maxunRealizedProfit_dict.get(symbol, 0)
            lowProfit = self.lowProfit_dict.get(symbol, 0)
            if self.unRealizedProfit_dict.get(symbol, 0) > 0:
                self.maxunRealizedProfit_dict[symbol] = max(maxunRealizedProfit, unRealizedProfit)
            elif self.unRealizedProfit_dict.get(symbol, 0) < 0:
                self.lowProfit_dict[symbol] = min(lowProfit, unRealizedProfit)

    def on_ticker_data(self, ticker):
        self.ticker_data(ticker)

    def ticker_data(self, ticker):
        symbol = ticker['symbol']
        if symbol in self.symbol_dict:
            self.last_price_dict[symbol] = float(ticker['last_price'])  # 最新的价格.
            if self.pos_dict.get(symbol, 0) != 0:
                if self.high_price_dict.get(symbol, 0.0) > 0.0:
                    self.high_price_dict[symbol] = max(self.high_price_dict.get(symbol, 0.0),
                                                       self.last_price_dict.get(symbol, 0.0))
                if self.low_price_dict.get(symbol, 0.0) > 0.0:
                    self.low_price_dict[symbol] = min(self.low_price_dict.get(symbol, 0.0),
                                                      self.last_price_dict.get(symbol, 0.0))
            now_enter_price = self.enter_price_dict.get(symbol, 0)
            if self.pos_dict.get(symbol, 0) == 0:  # 无持仓
                if self.order_flag_dict.get(symbol, 0) > self.last_price_dict.get(symbol, 0) > 0:
                    trading_size = self.trading_size_dict.get(symbol, 0)
                    res_buy = self.buy(symbol, 100, trading_size, mark=True)
                    self.dingding(f'回补开仓返回:{res_buy}', symbol)
                    self.enter_price_dict[symbol] = 0
                    self.pos_dict[symbol] = trading_size
                    self.high_price_dict[symbol] = 0
                    self.low_price_dict[symbol] = 0
                    self.maxunRealizedProfit_dict[symbol] = 0
                    self.unRealizedProfit_dict[symbol] = 0
                    self.lowProfit_dict[symbol] = 0
                    HYJ_jd_first = f'回补仓位,{symbol},last_price:{self.last_price_dict.get(symbol, 0)}'
                    HYJ_jd_tradeType = '补仓'
                    HYJ_jd_curAmount = f'{self.order_flag_dict.get(symbol)}'
                    HYJ_jd_remark = f'回补仓位,留意仓位:{trading_size}'
                    if "code" in res_buy:
                        HYJ_jd_remark += f'{res_buy}'
                    self.wx_send_msg(HYJ_jd_first, HYJ_jd_tradeType, HYJ_jd_curAmount, HYJ_jd_remark)

            elif self.pos_dict.get(symbol, 0) > 0 and now_enter_price > 0:  # 多单持仓
                if self.last_price_dict.get(symbol, 0) > self.win_price_dict.get(symbol, 0) > 0:
                    self.enter_price_dict[symbol] = 0
                    trading_size = self.pos_dict.get(symbol)
                    self.pos_dict[symbol] = 0
                    res_sell = self.sell(symbol, 100, trading_size, mark=True)
                    rt = (self.last_price_dict.get(symbol, 0) - now_enter_price) * trading_size
                    Profit = self.round_to(rt, self.min_price)
                    self.dingding(f"止盈平多,交易所返回:{res_sell}", symbols=symbol)
                    HYJ_jd_first = "止盈平多:交易对:%s,最大浮亏损:%s,最大浮利润:%s,当前浮利润:%s,仓位:%s" % (
                        symbol, self.lowProfit_dict.get(symbol, 0), self.maxunRealizedProfit_dict.get(symbol, 0),
                        self.unRealizedProfit_dict.get(symbol, 0), trading_size)
                    HYJ_jd_tradeType = "止盈"
                    HYJ_jd_curAmount = f"{now_enter_price}"
                    HYJ_jd_remark = "预计利润:%s,最新价:%s,最高价:%s,最低价:%s" % (
                        Profit, self.last_price_dict.get(symbol, 0), self.high_price_dict.get(symbol, 0),
                        self.low_price_dict.get(symbol, 0))
                    if "code" in res_sell:
                        HYJ_jd_remark += f'{res_sell}'
                    self.high_price_dict[symbol] = 0
                    self.low_price_dict[symbol] = 0
                    self.maxunRealizedProfit_dict[symbol] = 0
                    self.unRealizedProfit_dict[symbol] = 0
                    self.lowProfit_dict[symbol] = 0
                    self.wx_send_msg(HYJ_jd_first, HYJ_jd_tradeType, HYJ_jd_curAmount, HYJ_jd_remark)
            elif self.pos_dict.get(symbol, 0) < 0:  # 空单持仓
                res_buy = self.buy(symbol, 100, abs(self.pos_dict.get(symbol, 0)), mark=True)
                self.pos_dict[symbol] = 0
                self.dingding(f'平空返回:{res_buy}', symbol)
                HYJ_jd_first = f'平空,{symbol},last_price:{self.last_price_dict.get(symbol, 0)}'
                HYJ_jd_tradeType = '平空'
                HYJ_jd_curAmount = f'{self.order_flag_dict.get(symbol)}'
                HYJ_jd_remark = f'平空,留意仓位, enter_price:{now_enter_price}'
                if "code" in res_buy:
                    HYJ_jd_remark += f'{res_buy}'
                self.enter_price_dict[symbol] = 0
                self.high_price_dict[symbol] = 0
                self.low_price_dict[symbol] = 0
                self.maxunRealizedProfit_dict[symbol] = 0
                self.unRealizedProfit_dict[symbol] = 0
                self.lowProfit_dict[symbol] = 0
                self.wx_send_msg(HYJ_jd_first, HYJ_jd_tradeType, HYJ_jd_curAmount, HYJ_jd_remark)

            if self.tactics_flag == 1:
                print(f'{symbol}', 'ws接收数据成功')

# -*- coding: utf-8 -*-
##############################################################################
# Author：QQ173782910
##############################################################################
import redis
import json
import pytz
# 注意：
#    持仓方向为单向,不会设置杠杆
#    下边的dingding_token,wx_openid为空的话是不会发送钉钉消息和公众号消息

version_flag = '20211024'

with open(r'config.json', encoding='utf-8') as config_file:
    config_dict = json.load(config_file)
with open(r'symbol_metas.json', encoding='utf-8') as symbol_metas_file:
    symbol_metas_dict = json.load(symbol_metas_file)
    config_dict['trade']['strategy']['symbol_metas'] = symbol_metas_dict

config_raw = config_dict
timezone = pytz.timezone(config_dict['system']['timezone'])
print_error = config_dict['system']['print_error']

key = config_dict['trade']['exchange']['access_key']  # 币安API的key
secret = config_dict['trade']['exchange']['access_secret']  # 币安API的secret

dingding_token = config_dict['notify']['ding_talk_token']  # 钉钉webhook的access_token
wx_openid = config_dict['notify']['wechat_open_id']  # 关注简道斋后发送openid得到的那一串字符就是这个

trade_size_factor = config_dict['trade']['trade_size_factor']
tactics_flag = config_dict['notify']['tactics_flag']  # 机器人消息参数，1为钉钉确认策略计算是否正常，2为钉钉确认ws接收数据是否正常，
# 机器人消息参数  3为打印确认ws接收数据是否正常,4为打印确认策略计算是否正常。
add_pos_flag = config_dict['trade']['add_pos_flag']  # 加仓标识，为1开启，0关闭,加仓是当币在扛单中，再次遇到开仓信号就又开一次仓，这样会降低持仓均价，但爆仓风险更大
add_pos_amount = config_dict['trade']['add_pos_amount']  # 加仓次数，0不限次数，其他的整数值为最大加仓次数，每个币的次数一样，不单独设置

kline_source = config_dict['trade']['kline_source']
record_trade = config_dict['trade']['record']

trade_klines_fetch_worker = config_dict['system']['redis_klines_web_fetch_worker']
redis_namespace = config_dict['system']['redis_klines_namespace']

redis_config = config_dict['system']['redis']
redis_pool = redis.ConnectionPool(host=redis_config['host'], port=redis_config['port'],
                                  db=redis_config['db_index'], password=redis_config['password'])
redisc = redis.StrictRedis(connection_pool=redis_pool)


def get_symbol_metas(group_name: str = 'customized'):
    _strategy_config = config_dict['trade']['strategy']
    _symbol_metas = _strategy_config['symbol_metas']
    _symbols = _symbol_metas.keys()
    if not _strategy_config['select_all_symbols']:
        _symbols = _strategy_config['select_symbol_groups'][group_name]

    return {symbol: meta for symbol, meta in _symbol_metas.items() if symbol in _symbols}

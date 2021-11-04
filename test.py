import json
import time
from collections import defaultdict
from decimal import Decimal

from RunUse.AbstractTradeRun import AbstractTradeRun
from RunUse.model.symbol_position import SymbolPosition
from config import redisc

from apscheduler.schedulers.background import BlockingScheduler

from getaway.redis_wrapper_binance_http import RedisWrapperBinanceFutureHttp


def print_config():
    metas = [["AAVEUSDT", 0.2, 1.007, 0.972], ["KSMUSDT", 0.3, 1.007, 0.972], ["UNIUSDT", 1.0, 1.007, 0.972],
             ["EGLDUSDT", 0.6, 1.01, 0.972], ["BNBUSDT", 0.03, 1.007, 0.972], ["SOLUSDT", 1, 1.01, 0.972],
             ["DOTUSDT", 0.6, 1.007, 0.972], ["BTCUSDT", 0.001, 1.01, 0.972], ["YFIUSDT", 0.002, 1.007, 0.972],
             ["ETHUSDT", 0.002, 1.007, 0.972], ["LTCUSDT", 0.03, 1.007, 0.972], ["BCHUSDT", 0.08, 1.007, 0.972],
             ["MKRUSDT", 0.005, 1.007, 0.972], ["DASHUSDT", 0.09, 1.007, 0.972], ["ZECUSDT", 0.5, 1.007, 0.972],
             ["ZENUSDT", 0.3, 1.007, 0.972], ["FILUSDT", 0.4, 1.007, 0.972], ["AVAXUSDT", 1, 1.007, 0.972],
             ["LUNAUSDT", 2, 1.007, 0.972], ["YFIIUSDT", 0.003, 1.006, 0.972], ["COMPUSDT", 0.03, 1.007, 0.972],
             ["XMRUSDT", 0.05, 1.007, 0.972], ["TRBUSDT", 0.5, 1.007, 0.972], ["NEOUSDT", 0.5, 1.007, 0.972],
             ["NEARUSDT", 4.0, 1.007, 0.972], ["ATOMUSDT", 0.5, 1.007, 0.972], ["AXSUSDT", 2, 1.007, 0.972],
             ["ICPUSDT", 0.6, 1.007, 0.972], ["WAVESUSDT", 0.6, 1.007, 0.972], ["LINKUSDT", 0.6, 1.007, 0.972],
             ["BALUSDT", 0.6, 1.007, 0.972], ["HNTUSDT", 2, 1.007, 0.972], ["DYDXUSDT", 1.1, 1.007, 0.972],
             ["ALICEUSDT", 1.2, 1.007, 0.972], ["SNXUSDT", 1.1, 1.007, 0.972], ["QTUMUSDT", 1.2, 1.007, 0.972],
             ["RAYUSDT", 0.9, 1.007, 0.972], ["SUSHIUSDT", 3, 1.007, 0.972], ["OMGUSDT", 1.2, 1.007, 0.972],
             ["MASKUSDT", 2, 1.007, 0.972], ["UNFIUSDT", 1.2, 1.007, 0.972], ["SRMUSDT", 3, 1.007, 0.972],
             ["GTCUSDT", 1.5, 1.007, 0.97], ["RUNEUSDT", 3, 1.007, 0.972], ["BANDUSDT", 2, 1.007, 0.972],
             ["XTZUSDT", 3, 1.007, 0.972], ["THETAUSDT", 3, 1.007, 0.972], ["KAVAUSDT", 3, 1.007, 0.972],
             ["ARUSDT", 0.4, 1.007, 0.972], ["CELOUSDT", 2, 1.007, 0.972], ["RLCUSDT", 2.5, 1.007, 0.972],
             ["LITUSDT", 2.5, 1.007, 0.972], ["C98USDT", 3, 1.007, 0.972], ["MTLUSDT", 3, 1.007, 0.972],
             ["1INCHUSDT", 3, 1.007, 0.972], ["CRVUSDT", 7.1, 1.007, 0.972], ["SXPUSDT", 3.6, 1.007, 0.972],
             ["AUDIOUSDT", 4, 1.007, 0.972], ["TOMOUSDT", 4, 1.007, 0.972], ["ADAUSDT", 4, 1.007, 0.972],
             ["ICXUSDT", 4, 1.007, 0.972], ["BAKEUSDT", 4, 1.007, 0.972], ["BELUSDT", 4, 1.007, 0.972],
             ["ALGOUSDT", 5, 1.007, 0.972], ["CTKUSDT", 8, 1.007, 0.972], ["KNCUSDT", 4, 1.007, 0.972],
             ["ENJUSDT", 9, 1.007, 0.972], ["FTMUSDT", 9, 1.007, 0.972], ["DODOUSDT", 9.6, 1.007, 0.972],
             ["MATICUSDT", 7, 1.007, 0.972], ["IOTAUSDT", 6.7, 1.007, 0.972], ["STORJUSDT", 8, 1.007, 0.972],
             ["XRPUSDT", 9, 1.007, 0.972], ["RENUSDT", 9, 1.007, 0.972], ["SFPUSDT", 9, 1.007, 0.972],
             ["ZRXUSDT", 10.3, 1.007, 0.972], ["ALPHAUSDT", 10, 1.007, 0.972], ["ATAUSDT", 10, 1.007, 0.972],
             ["ONTUSDT", 9.5, 1.007, 0.972], ["OGNUSDT", 10, 1.007, 0.972], ["SANDUSDT", 10, 1.007, 0.972],
             ["MANAUSDT", 12, 1.007, 0.972], ["GRTUSDT", 18, 1.007, 0.972], ["OCEANUSDT", 11, 1.007, 0.972],
             ["BATUSDT", 12.4, 1.007, 0.972], ["CVCUSDT", 16, 1.007, 0.972], ["FLMUSDT", 16, 1.007, 0.972],
             ["KEEPUSDT", 20, 1.007, 0.972], ["LRCUSDT", 26, 1.007, 0.972], ["HBARUSDT", 26, 1.007, 0.972],
             ["CHRUSDT", 28, 1.007, 0.972], ["SKLUSDT", 29, 1.007, 0.972], ["NKNUSDT", 26, 1.007, 0.972],
             ["XLMUSDT", 27, 1.007, 0.972], ["BZRXUSDT", 30, 1.007, 0.972], ["CHZUSDT", 45, 1.007, 0.972],
             ["1000XECUSDT", 37, 1.007, 0.972], ["BLZUSDT", 68, 1.007, 0.972], ["DOGEUSDT", 34, 1.007, 0.972],
             ["TLMUSDT", 40, 1.007, 0.972], ["ONEUSDT", 85, 1.007, 0.972], ["XEMUSDT", 56, 1.007, 0.972],
             ["CELRUSDT", 64, 1.007, 0.972], ["VETUSDT", 147, 1.007, 0.972], ["RVNUSDT", 74, 1.007, 0.972],
             ["GALAUSDT", 151, 1.007, 0.972], ["ZILUSDT", 92, 1.007, 0.972], ["TRXUSDT", 93, 1.007, 0.972],
             ["ANKRUSDT", 99, 1.007, 0.972], ["IOSTUSDT", 161, 1.007, 0.972], ["DGBUSDT", 336, 1.007, 0.972],
             ["RSRUSDT", 258, 1.007, 0.972], ["LINAUSDT", 187, 1.007, 0.972], ["BTSUSDT", 388, 1.007, 0.972],
             ["STMXUSDT", 283, 1.007, 0.972], ["AKROUSDT", 459, 1.007, 0.972], ["SCUSDT", 925, 1.007, 0.972],
             ["1000SHIBUSDT", 305, 1.0075, 0.972], ["DENTUSDT", 1500, 1.007, 0.972]]
    strategy_config = {
        "minute_1": [
            ["AAVEUSDT", 24, 10], ["KSMUSDT", 22, 2], ["UNIUSDT", 27, 42], ["EGLDUSDT", 25.5, 50],
            ["BNBUSDT", 23, 25], ["SOLUSDT", 25, -10], ["DOTUSDT", 24, 17], ["YFIUSDT", 21, 150],
            ["ETHUSDT", 26, 80], ["LTCUSDT", 27, 75], ["BCHUSDT", 22, 24], ["MKRUSDT", 24, -10],
            ["DASHUSDT", 23, -30], ["ZECUSDT", 24, 38], ["ZENUSDT", 24, 49], ["FILUSDT", 21, 34],
            ["AVAXUSDT", 28, -20], ["LUNAUSDT", 25, -28], ["YFIIUSDT", 24, -41], ["COMPUSDT", 24, -11],
            ["XMRUSDT", 18, 100], ["TRBUSDT", 21, 118], ["NEOUSDT", 25, 13], ["NEARUSDT", 25, 61],
            ["ATOMUSDT", 23, 59], ["AXSUSDT", 23, 82], ["ICPUSDT", 24, 150], ["WAVESUSDT", 24, 17],
            ["LINKUSDT", 22, 5], ["BALUSDT", 22, 46], ["HNTUSDT", 23, 200], ["DYDXUSDT", 22, 100],
            ["ALICEUSDT", 21, 150], ["SNXUSDT", 26, -30], ["QTUMUSDT", 20, 150], ["RAYUSDT", 26, 150],
            ["SUSHIUSDT", 23, 295], ["OMGUSDT", 23, 500], ["MASKUSDT", 24, 154], ["UNFIUSDT", 24, -10],
            ["SRMUSDT", 24, 150], ["GTCUSDT", 24, 74], ["RUNEUSDT", 24, 67], ["BANDUSDT", 25, -39],
            ["XTZUSDT", 19, -92], ["THETAUSDT", 26, 22], ["KAVAUSDT", 18, 427], ["BTCUSDT", 22, 115],

            ["LRCUSDT", 25, 501], ["HBARUSDT", 26, -50], ["CHRUSDT", 27, 86], ["SKLUSDT", 24, 90],
            ["NKNUSDT", 25, 94], ["XLMUSDT", 26, -10], ["BZRXUSDT", 26, 15], ["CHZUSDT", 27, 100],
            ["1000XECUSDT", 27, -15], ["BLZUSDT", 23, 35], ["DOGEUSDT", 22, 700], ["TLMUSDT", 25, 100],
            ["ONEUSDT", 27, -4], ["XEMUSDT", 27, 35], ["CELRUSDT", 30, -33], ["VETUSDT", 29, 30],
            ["RVNUSDT", 27, 5], ["GALAUSDT", 26, 20], ["ZILUSDT", 23, -25], ["TRXUSDT", 21, -20],
            ["ANKRUSDT", 21, -2], ["IOSTUSDT", 23, 80], ["DGBUSDT", 23, -30], ["RSRUSDT", 23, -30],
            ["LINAUSDT", 26, 60], ["BTSUSDT", 26, 60], ["STMXUSDT", 22, 25], ["AKROUSDT", 24, 110],
            ["SCUSDT", 22, 300], ["1000SHIBUSDT", 24, 300], ["DENTUSDT", 28, -30],

            ["ARUSDT", 23, -68], ["CELOUSDT", 25, -62], ["RLCUSDT", 24, 14], ["LITUSDT", 23, 199],
            ["C98USDT", 25, 28], ["MTLUSDT", 24, 350], ["1INCHUSDT", 27, -11], ["CRVUSDT", 21, 650],
            ["SXPUSDT", 27, 58], ["AUDIOUSDT", 27, 200], ["TOMOUSDT", 28, 220], ["ADAUSDT", 23, 150],
            ["ICXUSDT", 23, 41], ["BAKEUSDT", 22, -7], ["BELUSDT", 23, 32], ["ALGOUSDT", 23, 71],
            ["CTKUSDT", 22, 110], ["KNCUSDT", 28, 31], ["ENJUSDT", 25, 33], ["FTMUSDT", 26, 350],
            ["DODOUSDT", 25, 350], ["MATICUSDT", 23, -20], ["IOTAUSDT", 20, 200], ["STORJUSDT", 25, 98],
            ["XRPUSDT", 27, -1], ["RENUSDT", 23, 45], ["SFPUSDT", 26, -23], ["ZRXUSDT", 22, 150],
            ["ALPHAUSDT", 22, 85], ["ATAUSDT", 28, -10], ["ONTUSDT", 21, 200], ["OGNUSDT", 25, 100],
            ["SANDUSDT", 23, 200], ["MANAUSDT", 26, -50], ["GRTUSDT", 24, 21], ["OCEANUSDT", 23, 35],
            ["BATUSDT", 23, 52], ["CVCUSDT", 22, -3], ["FLMUSDT", 25, 200], ["KEEPUSDT", 24, 200]
        ],
        "minute_3": [
            ["AAVEUSDT", 28, 20], ["KSMUSDT", 27, -10], ["UNIUSDT", 29, 13], ["EGLDUSDT", 30, -20],
            ["BNBUSDT", 27, 24], ["SOLUSDT", 29, 20], ["DOTUSDT", 29, 95], ["YFIUSDT", 29, 10],
            ["ETHUSDT", 28, -12], ["LTCUSDT", 29, -13], ["BCHUSDT", 23, -15], ["MKRUSDT", 27, 2],
            ["DASHUSDT", 29, -15], ["ZECUSDT", 26, 22], ["ZENUSDT", 26, 8], ["FILUSDT", 28, -24],
            ["AVAXUSDT", 27, -19], ["LUNAUSDT", 21, -20], ["YFIIUSDT", 27, 30], ["COMPUSDT", 27, -6],
            ["XMRUSDT", 25, 21], ["TRBUSDT", 25, 186], ["NEOUSDT", 28, 20], ["NEARUSDT", 27, 7],
            ["ATOMUSDT", 24.5, 13], ["AXSUSDT", 27, -30], ["ICPUSDT", 27, -42], ["WAVESUSDT", 25, -20],
            ["LINKUSDT", 27, -14], ["BALUSDT", 24, -50], ["HNTUSDT", 23, 150], ["DYDXUSDT", 26, 200],
            ["ALICEUSDT", 23, 150], ["SNXUSDT", 27, 105], ["QTUMUSDT", 27, 150], ["RAYUSDT", 24, 150],
            ["SUSHIUSDT", 27, 114], ["OMGUSDT", 26, 300], ["MASKUSDT", 24, 350], ["UNFIUSDT", 24, 218],
            ["SRMUSDT", 26, 65], ["GTCUSDT", 29, 400], ["RUNEUSDT", 25, 126], ["BANDUSDT", 27, 245],
            ["XTZUSDT", 24, 46], ["THETAUSDT", 25, -22], ["KAVAUSDT", 18, 62], ["BTCUSDT", 22, -62],

            ["LRCUSDT", 26, -7], ["HBARUSDT", 28, 60], ["CHRUSDT", 26, 25], ["SKLUSDT", 26, 100],
            ["NKNUSDT", 24, 78], ["XLMUSDT", 26, 70], ["BZRXUSDT", 27, 150], ["CHZUSDT", 28, 100],
            ["1000XECUSDT", 27, -15], ["BLZUSDT", 26, 150], ["DOGEUSDT", 22, -15], ["TLMUSDT", 30, -23],
            ["ONEUSDT", 25, 33], ["XEMUSDT", 30, 50], ["CELRUSDT", 30, 46], ["VETUSDT", 30, 150],
            ["RVNUSDT", 27, 100], ["GALAUSDT", 26, 80], ["ZILUSDT", 26, 80], ["TRXUSDT", 25, 100],
            ["ANKRUSDT", 25, 50], ["IOSTUSDT", 27, 15], ["DGBUSDT", 23, 60], ["RSRUSDT", 24, -30],
            ["LINAUSDT", 27, 50], ["BTSUSDT", 27, 50], ["STMXUSDT", 24, -20], ["AKROUSDT", 26, 35],
            ["SCUSDT", 23, 100], ["1000SHIBUSDT", 28, -50], ["DENTUSDT", 29, 25],

            ["ARUSDT", 24, 400], ["CELOUSDT", 22, 41], ["RLCUSDT", 25, -25], ["LITUSDT", 25, 68],
            ["C98USDT", 31, 250], ["MTLUSDT", 23, -41], ["1INCHUSDT", 27, -4], ["CRVUSDT", 23, 10],
            ["SXPUSDT", 27, 474], ["AUDIOUSDT", 29, -60], ["TOMOUSDT", 28, 150], ["ADAUSDT", 27, 50],
            ["ICXUSDT", 23, 120], ["BAKEUSDT", 28, -32], ["BELUSDT", 27, 250], ["ALGOUSDT", 26, 100],
            ["CTKUSDT", 26, 12], ["KNCUSDT", 26, 160], ["ENJUSDT", 28, 18], ["FTMUSDT", 29, 64],
            ["DODOUSDT", 26, 150], ["MATICUSDT", 28, 100], ["IOTAUSDT", 20, 1], ["STORJUSDT", 25, -60],
            ["XRPUSDT", 23, -34], ["RENUSDT", 27, 20], ["SFPUSDT", 21, 60], ["ZRXUSDT", 24, -8],
            ["ALPHAUSDT", 24, 21], ["ATAUSDT", 28, 140], ["ONTUSDT", 28, 50], ["OGNUSDT", 24, 32],
            ["SANDUSDT", 26, -45], ["MANAUSDT", 29, 92], ["GRTUSDT", 22, -50], ["OCEANUSDT", 24, 100],
            ["BATUSDT", 23, 30], ["CVCUSDT", 24, 110], ["FLMUSDT", 26, -20], ["KEEPUSDT", 28, 50]
        ],
        "minute_5": [
            ["AAVEUSDT", 31, 4], ["KSMUSDT", 27, 4], ["UNIUSDT", 31.5, 53], ["EGLDUSDT", 30, 10],
            ["BNBUSDT", 32, 36], ["SOLUSDT", 31, 41], ["DOTUSDT", 30, 25], ["YFIUSDT", 30, 45],
            ["ETHUSDT", 28, -12], ["LTCUSDT", 29, -12], ["BCHUSDT", 29, 150], ["MKRUSDT", 30, 145],
            ["DASHUSDT", 29, -10], ["ZECUSDT", 29, 18], ["ZENUSDT", 27, -31], ["FILUSDT", 28, 131],
            ["AVAXUSDT", 28, -26], ["LUNAUSDT", 27, 59], ["YFIIUSDT", 29, -52], ["COMPUSDT", 27, -41],
            ["XMRUSDT", 26, 230], ["TRBUSDT", 26, 5], ["NEOUSDT", 28, 38], ["NEARUSDT", 28, -24],
            ["ATOMUSDT", 25.5, 62], ["AXSUSDT", 28, 67], ["ICPUSDT", 28, 33], ["WAVESUSDT", 25, -41],
            ["LINKUSDT", 28, 58], ["BALUSDT", 26, 80], ["HNTUSDT", 23, -22], ["DYDXUSDT", 24, 86],
            ["ALICEUSDT", 24, 100], ["SNXUSDT", 28, 90], ["QTUMUSDT", 24, 62], ["RAYUSDT", 28, -10],
            ["SUSHIUSDT", 27, -27], ["OMGUSDT", 26, 47], ["MASKUSDT", 25, 178], ["UNFIUSDT", 24, -58],
            ["SRMUSDT", 25, 155], ["GTCUSDT", 29, -15], ["RUNEUSDT", 28, 42], ["BANDUSDT", 30, 183],
            ["XTZUSDT", 25, 200], ["THETAUSDT", 29, 189], ["KAVAUSDT", 24, 85], ["BTCUSDT", 30, -25],

            ["LRCUSDT", 26, 93], ["HBARUSDT", 28, 23], ["CHRUSDT", 27, 25], ["SKLUSDT", 26, 35],
            ["NKNUSDT", 27, 83], ["XLMUSDT", 30, 41], ["BZRXUSDT", 30, 44], ["CHZUSDT", 27, 35],
            ["1000XECUSDT", 27, 100], ["BLZUSDT", 30, 90], ["DOGEUSDT", 26, 55], ["TLMUSDT", 30, 85],
            ["ONEUSDT", 29, -17], ["XEMUSDT", 30, -35], ["CELRUSDT", 28, 100], ["VETUSDT", 29, -22],
            ["RVNUSDT", 28, 41], ["GALAUSDT", 27, 25], ["ZILUSDT", 30, 11], ["TRXUSDT", 26, -45],
            ["ANKRUSDT", 28, 50], ["IOSTUSDT", 28, 80], ["DGBUSDT", 25, 27], ["RSRUSDT", 26, 70],
            ["LINAUSDT", 27, 60], ["BTSUSDT", 27, -22], ["STMXUSDT", 26, 80], ["AKROUSDT", 27, 17],
            ["SCUSDT", 25, -19], ["1000SHIBUSDT", 28, -20], ["DENTUSDT", 31, -20],

            ["ARUSDT", 24, 350], ["CELOUSDT", 24, -52], ["RLCUSDT", 29, 42], ["LITUSDT", 26, 43],
            ["C98USDT", 30, 250], ["MTLUSDT", 31, 130], ["1INCHUSDT", 26, 44], ["CRVUSDT", 25, 8],
            ["SXPUSDT", 27, 133], ["AUDIOUSDT", 28, 15], ["TOMOUSDT", 29, 5], ["ADAUSDT", 25, 150],
            ["ICXUSDT", 25.5, -28], ["BAKEUSDT", 23, -4], ["BELUSDT", 28, 37], ["ALGOUSDT", 27, 95],
            ["CTKUSDT", 26, 35], ["KNCUSDT", 27, 53], ["ENJUSDT", 28, 35], ["FTMUSDT", 29, -13],
            ["DODOUSDT", 28, 150], ["MATICUSDT", 28, 120], ["IOTAUSDT", 27, 28], ["STORJUSDT", 22, 90],
            ["XRPUSDT", 29, 35], ["RENUSDT", 28, 63], ["SFPUSDT", 25, -55], ["ZRXUSDT", 24, -4],
            ["ALPHAUSDT", 26, 63], ["ATAUSDT", 28, -20], ["ONTUSDT", 28, 100], ["OGNUSDT", 24, -35],
            ["SANDUSDT", 29, -33], ["MANAUSDT", 29, -10], ["GRTUSDT", 20, 250], ["OCEANUSDT", 25.5, -10],
            ["BATUSDT", 32, -20], ["CVCUSDT", 25, 94], ["FLMUSDT", 27, 85], ["KEEPUSDT", 28, 150]
        ],
        "minute_15": [
            ["AAVEUSDT", 32, 15], ["KSMUSDT", 27, 12], ["UNIUSDT", 26, -10], ["EGLDUSDT", 30, 50],
            ["BNBUSDT", 35, -20], ["SOLUSDT", 31, 91], ["DOTUSDT", 30, 50], ["YFIUSDT", 35, 90],
            ["ETHUSDT", 33, -5], ["LTCUSDT", 30, -25], ["BCHUSDT", 30, -5], ["MKRUSDT", 32, -22],
            ["DASHUSDT", 31, -8], ["ZECUSDT", 27, 6], ["ZENUSDT", 28, 68], ["FILUSDT", 29, 40],
            ["AVAXUSDT", 28, 44], ["LUNAUSDT", 28, 178], ["YFIIUSDT", 29, 83], ["COMPUSDT", 30, -21],
            ["XMRUSDT", 25, -39], ["TRBUSDT", 28, 84], ["NEOUSDT", 28, -3], ["NEARUSDT", 28, 69],
            ["ATOMUSDT", 27, -20], ["AXSUSDT", 29, 166], ["ICPUSDT", 28, 220], ["WAVESUSDT", 27, 75],
            ["LINKUSDT", 29, 57], ["BALUSDT", 27, 110], ["HNTUSDT", 28, 14], ["DYDXUSDT", 28, 60],
            ["ALICEUSDT", 24, 60], ["SNXUSDT", 28, 22], ["QTUMUSDT", 27, -11], ["RAYUSDT", 28, -38],
            ["SUSHIUSDT", 27, 245], ["OMGUSDT", 26, 113], ["MASKUSDT", 26, 111], ["UNFIUSDT", 24, 94],
            ["SRMUSDT", 27, 80], ["GTCUSDT", 28, 72], ["RUNEUSDT", 28, 55], ["BANDUSDT", 30, 80],
            ["XTZUSDT", 27, -23], ["THETAUSDT", 28, 44], ["KAVAUSDT", 27, 38], ["BTCUSDT", 25, 71],

            ["LRCUSDT", 26, -16], ["HBARUSDT", 29, 25], ["CHRUSDT", 27, 85], ["SKLUSDT", 26, 20],
            ["NKNUSDT", 27, 100], ["XLMUSDT", 29, 47], ["BZRXUSDT", 30, 100], ["CHZUSDT", 30, -30],
            ["1000XECUSDT", 28, -33], ["BLZUSDT", 30, 20], ["DOGEUSDT", 26, 100], ["TLMUSDT", 32, 100],
            ["ONEUSDT", 33, 58], ["XEMUSDT", 31, -6], ["CELRUSDT", 30, 30], ["VETUSDT", 30, -6],
            ["RVNUSDT", 29, -13], ["GALAUSDT", 28, -5], ["ZILUSDT", 30, 110], ["TRXUSDT", 27, 50],
            ["ANKRUSDT", 30, 80], ["IOSTUSDT", 29, 20], ["DGBUSDT", 30, 50], ["RSRUSDT", 26, 60],
            ["LINAUSDT", 30, 60], ["BTSUSDT", 28, 100], ["STMXUSDT", 27, 10], ["AKROUSDT", 28, 90],
            ["SCUSDT", 28, -20], ["1000SHIBUSDT", 28, 35], ["DENTUSDT", 31, 90],

            ["ARUSDT", 27, 165], ["CELOUSDT", 27, 136], ["RLCUSDT", 29, 88], ["LITUSDT", 29, 109],
            ["C98USDT", 30, 36], ["MTLUSDT", 29, 95], ["1INCHUSDT", 26, 100], ["CRVUSDT", 24, 10],
            ["SXPUSDT", 27, 85], ["AUDIOUSDT", 29, 100], ["TOMOUSDT", 26, 100], ["ADAUSDT", 26, 100],
            ["ICXUSDT", 27, -8], ["BAKEUSDT", 28, 200], ["BELUSDT", 28, 50], ["ALGOUSDT", 28, 110],
            ["CTKUSDT", 27, 21], ["KNCUSDT", 29, 95], ["ENJUSDT", 28, 54], ["FTMUSDT", 29, 92],
            ["DODOUSDT", 28, -10], ["MATICUSDT", 27, 100], ["IOTAUSDT", 25, -45], ["STORJUSDT", 26, -5],
            ["XRPUSDT", 26, -25], ["RENUSDT", 28, 104], ["SFPUSDT", 25, 150], ["ZRXUSDT", 26, 20],
            ["ALPHAUSDT", 25, 43], ["ATAUSDT", 28, 160], ["ONTUSDT", 28, -27], ["OGNUSDT", 27, -30],
            ["SANDUSDT", 30, -9], ["MANAUSDT", 26, -5], ["GRTUSDT", 23, 300], ["OCEANUSDT", 28, 62],
            ["BATUSDT", 31, 53], ["CVCUSDT", 27, -38], ["FLMUSDT", 28, 90], ["KEEPUSDT", 28, 85]
        ],
        "minute_30": [
            ["AAVEUSDT", 31, 10], ["KSMUSDT", 27, 2], ["UNIUSDT", 27, 15], ["EGLDUSDT", 30, 50],
            ["BNBUSDT", 32, 40], ["SOLUSDT", 31, 5], ["DOTUSDT", 30, 100], ["YFIUSDT", 33, 90],
            ["ETHUSDT", 33, -4], ["LTCUSDT", 29, 70], ["BCHUSDT", 32, -10], ["MKRUSDT", 31, 22],
            ["DASHUSDT", 30, 18], ["ZECUSDT", 30, 153], ["ZENUSDT", 31, 55], ["FILUSDT", 30, 68],
            ["AVAXUSDT", 29, 78], ["LUNAUSDT", 28, 78], ["YFIIUSDT", 30, 14], ["COMPUSDT", 30, 22],
            ["XMRUSDT", 30, 44], ["TRBUSDT", 29, 78], ["NEOUSDT", 29, 30], ["NEARUSDT", 30, 71],
            ["ATOMUSDT", 28, -19], ["AXSUSDT", 30, 51], ["ICPUSDT", 30, 77], ["WAVESUSDT", 28, 101],
            ["LINKUSDT", 29, 22], ["BALUSDT", 28, 39], ["HNTUSDT", 29, 83], ["DYDXUSDT", 28, 190],
            ["ALICEUSDT", 28, 100], ["SNXUSDT", 27, 27], ["QTUMUSDT", 27, 46], ["RAYUSDT", 28, 125],
            ["SUSHIUSDT", 27, 52], ["OMGUSDT", 26, -14], ["MASKUSDT", 26, 90], ["UNFIUSDT", 26, 92],
            ["SRMUSDT", 28, 59], ["GTCUSDT", 28, 175], ["RUNEUSDT", 28, 44], ["BANDUSDT", 30, 30],
            ["XTZUSDT", 29, -7], ["THETAUSDT", 27, 38], ["KAVAUSDT", 28, 57], ["BTCUSDT", 25, 68],

            ["LRCUSDT", 28, 20], ["HBARUSDT", 34, 51], ["CHRUSDT", 29, 69], ["SKLUSDT", 27, 27],
            ["NKNUSDT", 28, 35], ["XLMUSDT", 32, 31], ["BZRXUSDT", 30, 65], ["CHZUSDT", 33, 50],
            ["1000XECUSDT", 29, 100], ["BLZUSDT", 31, 55], ["DOGEUSDT", 28, 30], ["TLMUSDT", 32, 32],
            ["ONEUSDT", 33, 65], ["XEMUSDT", 33, 24], ["CELRUSDT", 31, 52], ["VETUSDT", 30, 32],
            ["RVNUSDT", 30, 25], ["GALAUSDT", 28, 80], ["ZILUSDT", 32, 25], ["TRXUSDT", 29, -3],
            ["ANKRUSDT", 31, 24], ["IOSTUSDT", 30, 36], ["DGBUSDT", 32, -22], ["RSRUSDT", 28, 35],
            ["LINAUSDT", 32, 70], ["BTSUSDT", 29, 140], ["STMXUSDT", 33, 30], ["AKROUSDT", 30, 55],
            ["SCUSDT", 29, 40], ["1000SHIBUSDT", 28, 70], ["DENTUSDT", 31, 50],

            ["ARUSDT", 27, 143], ["CELOUSDT", 31, 37], ["RLCUSDT", 29, 88], ["LITUSDT", 30, 94],
            ["C98USDT", 30, 300], ["MTLUSDT", 30, 120], ["1INCHUSDT", 26, 136], ["CRVUSDT", 27, -28],
            ["SXPUSDT", 27, 81], ["AUDIOUSDT", 30, 350], ["TOMOUSDT", 27, 72], ["ADAUSDT", 27, 25],
            ["ICXUSDT", 30, 51], ["BAKEUSDT", 31, 42], ["BELUSDT", 28, 85], ["ALGOUSDT", 30, 34],
            ["CTKUSDT", 27, -11], ["KNCUSDT", 30, 66], ["ENJUSDT", 29, 97], ["FTMUSDT", 29, 31],
            ["DODOUSDT", 29, 30], ["MATICUSDT", 30, 52], ["IOTAUSDT", 25, -20], ["STORJUSDT", 28, 130],
            ["XRPUSDT", 26, 100], ["RENUSDT", 31, 62], ["SFPUSDT", 25, 58], ["ZRXUSDT", 25, 50],
            ["ALPHAUSDT", 26, 230], ["ATAUSDT", 29, 76], ["ONTUSDT", 28, 53], ["OGNUSDT", 30, 85],
            ["SANDUSDT", 29, 35], ["MANAUSDT", 31, 43], ["GRTUSDT", 23, -10], ["OCEANUSDT", 28, -23],
            ["BATUSDT", 31, 130], ["CVCUSDT", 30, 55], ["FLMUSDT", 28, 77], ["KEEPUSDT", 29, 57]
        ],
        "hour_1": [
            ["AAVEUSDT", 30, 10], ["KSMUSDT", 29, 50], ["UNIUSDT", 30, 10], ["EGLDUSDT", 32, 20],
            ["BNBUSDT", 31, 50], ["SOLUSDT", 33, 20], ["DOTUSDT", 30, 42], ["YFIUSDT", 34, 90],
            ["ETHUSDT", 32, 40], ["LTCUSDT", 32, 80], ["BCHUSDT", 31, 33], ["MKRUSDT", 31, 24],
            ["DASHUSDT", 30, 23], ["ZECUSDT", 30, 45], ["ZENUSDT", 30, 21], ["FILUSDT", 29, 63],
            ["AVAXUSDT", 29, 10], ["LUNAUSDT", 30, 23], ["YFIIUSDT", 32, 31], ["COMPUSDT", 31, 34],
            ["XMRUSDT", 31, 24], ["TRBUSDT", 30, 5], ["NEOUSDT", 30, 26], ["NEARUSDT", 30, 15],
            ["ATOMUSDT", 29, 40], ["AXSUSDT", 32, 100], ["ICPUSDT", 31, 64], ["WAVESUSDT", 28, 1],
            ["LINKUSDT", 29, 12], ["BALUSDT", 29, 91], ["HNTUSDT", 31, 16], ["DYDXUSDT", 30, 4],
            ["ALICEUSDT", 29, 75], ["SNXUSDT", 27, -14], ["QTUMUSDT", 27, 14], ["RAYUSDT", 26, -25],
            ["SUSHIUSDT", 31, 21], ["OMGUSDT", 26, 101], ["MASKUSDT", 26, 38], ["UNFIUSDT", 26, 81],
            ["SRMUSDT", 28, 115], ["GTCUSDT", 28, 79], ["RUNEUSDT", 28, 89], ["BANDUSDT", 30, 29],
            ["XTZUSDT", 30, 54], ["THETAUSDT", 26, 34], ["KAVAUSDT", 30, 12], ["BTCUSDT", 25, 119, 3],

            ["LRCUSDT", 30, 29], ["HBARUSDT", 35, 30], ["CHRUSDT", 32, 47], ["SKLUSDT", 30, 19],
            ["NKNUSDT", 29, 11], ["XLMUSDT", 32, 43], ["BZRXUSDT", 32, 24], ["CHZUSDT", 34, 20],
            ["1000XECUSDT", 32, -23], ["BLZUSDT", 31, -20], ["DOGEUSDT", 28, 30], ["TLMUSDT", 34, 22],
            ["ONEUSDT", 33, 23], ["XEMUSDT", 31, -15], ["CELRUSDT", 31, 21], ["VETUSDT", 32, 55],
            ["RVNUSDT", 31, 21], ["GALAUSDT", 32, 35], ["ZILUSDT", 32, 31], ["TRXUSDT", 31, 14],
            ["ANKRUSDT", 32, 33], ["IOSTUSDT", 30, 35], ["DGBUSDT", 35, 45], ["RSRUSDT", 30, 13],
            ["LINAUSDT", 33, 36], ["BTSUSDT", 30, 45], ["STMXUSDT", 34, 29], ["AKROUSDT", 30, 180],
            ["SCUSDT", 30, 35], ["1000SHIBUSDT", 29, 25], ["DENTUSDT", 32, 10],

            ["ARUSDT", 30, 98], ["CELOUSDT", 33, 20], ["RLCUSDT", 29, -23], ["LITUSDT", 31, 63],
            ["C98USDT", 30, 32], ["MTLUSDT", 31, 70], ["1INCHUSDT", 26, 56], ["CRVUSDT", 27, 58],
            ["SXPUSDT", 27, -2], ["AUDIOUSDT", 30, 200], ["TOMOUSDT", 27, -7], ["ADAUSDT", 29, 50],
            ["ICXUSDT", 30, 26], ["BAKEUSDT", 31, 46], ["BELUSDT", 29, 31], ["ALGOUSDT", 31, 32],
            ["CTKUSDT", 27, -15], ["KNCUSDT", 30, 105], ["ENJUSDT", 30, -18], ["FTMUSDT", 31, 17],
            ["DODOUSDT", 29, 70], ["MATICUSDT", 30, 35], ["IOTAUSDT", 33, -22], ["STORJUSDT", 27, 43],
            ["XRPUSDT", 27, 65], ["RENUSDT", 31, 38], ["SFPUSDT", 29, 50], ["ZRXUSDT", 26, 39],
            ["ALPHAUSDT", 26, 50], ["ATAUSDT", 29, -15], ["ONTUSDT", 28, 52], ["OGNUSDT", 30, 43],
            ["SANDUSDT", 29, 33], ["MANAUSDT", 31, -15], ["GRTUSDT", 25, -30], ["OCEANUSDT", 30, 50],
            ["BATUSDT", 30, 36], ["CVCUSDT", 31, 47], ["FLMUSDT", 27, 21], ["KEEPUSDT", 30, 75]
        ],
        "hour_2": [
            ["AAVEUSDT", 32, 10], ["KSMUSDT", 30, 18], ["UNIUSDT", 32, 10], ["EGLDUSDT", 35, -10],
            ["BNBUSDT", 31, 100], ["SOLUSDT", 33, 30], ["DOTUSDT", 31, 50], ["YFIUSDT", 33, 45],
            ["ETHUSDT", 32, 150], ["LTCUSDT", 34, 140], ["BCHUSDT", 30, 115], ["MKRUSDT", 34, 39],
            ["DASHUSDT", 31, 62], ["ZECUSDT", 30, 45], ["ZENUSDT", 32, 9], ["FILUSDT", 30, 54],
            ["AVAXUSDT", 33, 14], ["LUNAUSDT", 30, 9], ["YFIIUSDT", 32, 6], ["COMPUSDT", 32, 21],
            ["XMRUSDT", 32, 64], ["TRBUSDT", 31, 5], ["NEOUSDT", 33, 150], ["NEARUSDT", 32, -21],
            ["ATOMUSDT", 31, 22], ["AXSUSDT", 32, 82], ["ICPUSDT", 28, 22], ["WAVESUSDT", 32, 24],
            ["LINKUSDT", 30, 50], ["BALUSDT", 30, 42], ["HNTUSDT", 32, 30], ["DYDXUSDT", 30, 150],
            ["ALICEUSDT", 30, 80], ["SNXUSDT", 27, -1], ["QTUMUSDT", 27, 70], ["RAYUSDT", 28, -40],
            ["SUSHIUSDT", 31, 21], ["OMGUSDT", 28, 76], ["MASKUSDT", 30, 3], ["UNFIUSDT", 26, 10],
            ["SRMUSDT", 28, -4], ["GTCUSDT", 28, 57], ["RUNEUSDT", 28, 70], ["BANDUSDT", 30, 21],
            ["XTZUSDT", 30, 42], ["THETAUSDT", 29, -21], ["KAVAUSDT", 30, -10], ["BTCUSDT", 25, 16],

            ["LRCUSDT", 30, 77], ["HBARUSDT", 34, -19], ["CHRUSDT", 33, 50], ["SKLUSDT", 31, 48],
            ["NKNUSDT", 30, 65], ["XLMUSDT", 32, 26], ["BZRXUSDT", 35, 15], ["CHZUSDT", 34, 100],
            ["1000XECUSDT", 34, -45], ["BLZUSDT", 32, 55], ["DOGEUSDT", 29, 60], ["TLMUSDT", 30, 100],
            ["ONEUSDT", 33, 42], ["XEMUSDT", 30, 31], ["CELRUSDT", 31, -13], ["VETUSDT", 32, 22],
            ["RVNUSDT", 31, 26], ["GALAUSDT", 33, 50], ["ZILUSDT", 34, 30], ["TRXUSDT", 32, 90],
            ["ANKRUSDT", 32, 100], ["IOSTUSDT", 31, 20], ["DGBUSDT", 35, 35], ["RSRUSDT", 33, 31],
            ["LINAUSDT", 34, 60], ["BTSUSDT", 33, 70], ["STMXUSDT", 34, 60], ["AKROUSDT", 32, 60],
            ["SCUSDT", 30, 36], ["1000SHIBUSDT", 33, 30], ["DENTUSDT", 32, 15],

            ["ARUSDT", 31, 16], ["CELOUSDT", 30, 50], ["RLCUSDT", 29, -20], ["LITUSDT", 32, 92],
            ["C98USDT", 34, 24], ["MTLUSDT", 34, 55], ["1INCHUSDT", 26, 75], ["CRVUSDT", 29, -12],
            ["SXPUSDT", 27, -11], ["AUDIOUSDT", 31, -20], ["TOMOUSDT", 27, -20], ["ADAUSDT", 31, 100],
            ["ICXUSDT", 31, 15], ["BAKEUSDT", 31, 47], ["BELUSDT", 31, 51], ["ALGOUSDT", 31, 46],
            ["CTKUSDT", 30, 29], ["KNCUSDT", 29, 55], ["ENJUSDT", 30, 91], ["FTMUSDT", 32, 28],
            ["DODOUSDT", 30, 31], ["MATICUSDT", 32, 50], ["IOTAUSDT", 33, -10], ["STORJUSDT", 28, 60],
            ["XRPUSDT", 27, 36], ["RENUSDT", 31, 93], ["SFPUSDT", 29, 78], ["ZRXUSDT", 30, 65],
            ["ALPHAUSDT", 27, 93], ["ATAUSDT", 31, 200], ["ONTUSDT", 31, 63], ["OGNUSDT", 25, 50],
            ["SANDUSDT", 29, 50], ["MANAUSDT", 31, 65], ["GRTUSDT", 26, 50], ["OCEANUSDT", 27, 70],
            ["BATUSDT", 30, 75], ["CVCUSDT", 31, 55], ["FLMUSDT", 27, 72], ["KEEPUSDT", 34, 75]
        ],
        "hour_4": [
            ["AAVEUSDT", 32, -4], ["KSMUSDT", 31, 17], ["UNIUSDT", 31, 15], ["EGLDUSDT", 33, 20],
            ["BNBUSDT", 31, 100], ["SOLUSDT", 33, 20], ["DOTUSDT", 35, 100], ["YFIUSDT", 33, 19],
            ["ETHUSDT", 33, 52], ["LTCUSDT", 33, 70], ["BCHUSDT", 31, 12], ["MKRUSDT", 35, 12],
            ["DASHUSDT", 31, 4], ["ZECUSDT", 33, 58], ["ZENUSDT", 33, 22], ["FILUSDT", 35, -9],
            ["AVAXUSDT", 35, -18], ["LUNAUSDT", 35, 55], ["YFIIUSDT", 34, 30], ["COMPUSDT", 34, 6],
            ["XMRUSDT", 33, 22], ["TRBUSDT", 34, 5], ["NEOUSDT", 34, 31], ["NEARUSDT", 32, 25],
            ["ATOMUSDT", 32, 18], ["AXSUSDT", 35, 6], ["ICPUSDT", 28, 70], ["WAVESUSDT", 35, -38],
            ["LINKUSDT", 35, 79], ["BALUSDT", 32, -5], ["HNTUSDT", 32, -50], ["DYDXUSDT", 32, 150],
            ["ALICEUSDT", 34, 100], ["SNXUSDT", 27, 109], ["QTUMUSDT", 27, 50], ["RAYUSDT", 30, -40],
            ["SUSHIUSDT", 31, 56], ["OMGUSDT", 28, -8], ["MASKUSDT", 30, 3], ["UNFIUSDT", 27, 111],
            ["SRMUSDT", 28, 100], ["GTCUSDT", 28, 55], ["RUNEUSDT", 28, -12], ["BANDUSDT", 30, 40],
            ["XTZUSDT", 30, 32], ["THETAUSDT", 30, 65], ["KAVAUSDT", 30, -14], ["BTCUSDT", 25, 299],

            ["LRCUSDT", 33, 28], ["HBARUSDT", 35, 25], ["CHRUSDT", 35, 28], ["SKLUSDT", 34, 45],
            ["NKNUSDT", 34, -11], ["XLMUSDT", 32, 55], ["BZRXUSDT", 34, 31], ["CHZUSDT", 34, 22],
            ["1000XECUSDT", 32, 45], ["BLZUSDT", 34, 31], ["DOGEUSDT", 34, 34], ["TLMUSDT", 33, 100],
            ["ONEUSDT", 33, 85], ["XEMUSDT", 33, 47], ["CELRUSDT", 33, 47], ["VETUSDT", 35, -3],
            ["RVNUSDT", 32, 30], ["GALAUSDT", 35, -30], ["ZILUSDT", 35, -2], ["TRXUSDT", 34, 35],
            ["ANKRUSDT", 33, 36], ["IOSTUSDT", 33, 25], ["DGBUSDT", 35, 50], ["RSRUSDT", 35, 30],
            ["LINAUSDT", 34, -5], ["BTSUSDT", 33, 25], ["STMXUSDT", 34, 27], ["AKROUSDT", 35, 21],
            ["SCUSDT", 30, 60], ["1000SHIBUSDT", 33, 25], ["DENTUSDT", 35, 53],

            ["ARUSDT", 31, 16], ["CELOUSDT", 30, 50], ["RLCUSDT", 29, 26], ["LITUSDT", 33, 91],
            ["C98USDT", 34, 24], ["MTLUSDT", 34, 15], ["1INCHUSDT", 29, 80], ["CRVUSDT", 29, 37],
            ["SXPUSDT", 27, -24], ["AUDIOUSDT", 34, -7], ["TOMOUSDT", 32, 35], ["ADAUSDT", 31, 30],
            ["ICXUSDT", 32, 13], ["BAKEUSDT", 35, 12], ["BELUSDT", 31, 110], ["ALGOUSDT", 31, 35],
            ["CTKUSDT", 30, 89], ["KNCUSDT", 29, 63], ["ENJUSDT", 31, 45], ["FTMUSDT", 33, 45],
            ["DODOUSDT", 34, 77], ["MATICUSDT", 32, 39], ["IOTAUSDT", 33, 75], ["STORJUSDT", 31, 60],
            ["XRPUSDT", 27, 150], ["RENUSDT", 32, -10], ["SFPUSDT", 30, 52], ["ZRXUSDT", 30, 89],
            ["ALPHAUSDT", 35, 55], ["ATAUSDT", 33, 150], ["ONTUSDT", 27, 130], ["OGNUSDT", 32, 40],
            ["SANDUSDT", 29, 23], ["MANAUSDT", 35, 32], ["GRTUSDT", 26, 50], ["OCEANUSDT", 30, -12],
            ["BATUSDT", 30, -10], ["CVCUSDT", 29, 73], ["FLMUSDT", 31, 63], ["KEEPUSDT", 34, 75]
        ]
    }

    format_strategy_config = {}
    for interval, interval_configs in strategy_config.items():
        if interval not in format_strategy_config:
            format_strategy_config[interval] = {}
        for interval_config in interval_configs:
            symbol, sold, contrast = interval_config[0], interval_config[1], interval_config[2]
            format_strategy_config[interval][symbol] = {
                "sold": int(sold),
                "contrast": int(contrast)
            }

    config_map = {}
    for meta in metas:
        symbol, order_quantity, profit_position, loss_position = meta[0], meta[1], meta[2], meta[3]
        config = {
            "trading_size": float(order_quantity),
            "win_arg": float(profit_position),
            "add_arg": float(loss_position),
            "interval": {
                "minute_1": {
                    "sold": format_strategy_config['minute_1'][symbol]['sold'],
                    "contrast": format_strategy_config['minute_1'][symbol]['contrast']
                },
                "minute_3": {
                    "sold": format_strategy_config['minute_3'][symbol]['sold'],
                    "contrast": format_strategy_config['minute_3'][symbol]['contrast']
                },
                "minute_5": {
                    "sold": format_strategy_config['minute_5'][symbol]['sold'],
                    "contrast": format_strategy_config['minute_5'][symbol]['contrast']
                },
                "minute_15": {
                    "sold": format_strategy_config['minute_15'][symbol]['sold'],
                    "contrast": format_strategy_config['minute_15'][symbol]['contrast']
                },
                "minute_30": {
                    "sold": format_strategy_config['minute_30'][symbol]['sold'],
                    "contrast": format_strategy_config['minute_30'][symbol]['contrast']
                },
                "hour_1": {
                    "sold": format_strategy_config['hour_1'][symbol]['sold'],
                    "contrast": format_strategy_config['hour_1'][symbol]['contrast']
                },
                "hour_2": {
                    "sold": format_strategy_config['hour_2'][symbol]['sold'],
                    "contrast": format_strategy_config['hour_2'][symbol]['contrast']
                },
                "hour_4": {
                    "sold": format_strategy_config['hour_4'][symbol]['sold'],
                    "contrast": format_strategy_config['hour_4'][symbol]['contrast']
                }
            }
        }
        config_map[symbol] = config
    print(config_map)


def print_selected_symbol_metas():
    with open(r'config.json') as config_file:
        config_dict = json.load(config_file)

    key = config_dict['trade']['exchange']['access_key']  # 币安API的key
    secret = config_dict['trade']['exchange']['access_secret']  # 币安API的secret

    dingding_token = config_dict['notify']['ding_talk_token']  # 钉钉webhook的access_token
    wx_openid = config_dict['notify']['wechat_open_id']  # 关注简道斋后发送openid得到的那一串字符就是这个

    tactics_flag = config_dict['notify']['tactics_flag']  # 机器人消息参数，1为钉钉确认策略计算是否正常，2为钉钉确认ws接收数据是否正常，
    # 机器人消息参数  3为打印确认ws接收数据是否正常,4为打印确认策略计算是否正常。
    add_pos_flag = config_dict['trade']['add_pos_flag']  # 加仓标识，为1开启，0关闭,加仓是当币在扛单中，再次遇到开仓信号就又开一次仓，这样会降低持仓均价，但爆仓风险更大
    add_pos_amount = config_dict['trade']['add_pos_amount']  # 加仓次数，0不限次数，其他的整数值为最大加仓次数，每个币的次数一样，不单独设置

    _strategy_config = config_dict['trade']['strategy']
    _symbol_metas = _strategy_config['symbol_metas']
    _symbols = _symbol_metas.keys()
    if not _strategy_config['select_all_symbols']:
        _symbols = _strategy_config['select_symbol_groups']['customized']

    symbol_metas = {symbol: meta for symbol, meta in _symbol_metas.items() if symbol in _symbols}
    print(symbol_metas)


def zfill_numbers():
    numbers = [str(i).zfill(2) for i in range(0, 60, 15)]
    print(numbers)


def scheduler_test():
    scheduler = BlockingScheduler()  # 定时的任务.
    scheduler.add_job(lambda: print("2"), trigger='cron', id='TradeRunS1_1', second='2')  # 1min
    scheduler.add_job(lambda: print("10"), trigger='cron', id='TradeRunSp', second='*/10')
    scheduler.start()


def fetch_klines():
    invoker = RedisWrapperBinanceFutureHttp(redisc)
    data = invoker.get_kline_interval('BTCUSDT', '1m', limit=2)
    print(data)

def format_trade_size():
    trading_size = -216.123
    trading_size_str = str(trading_size)
    if trading_size_str.__contains__('.'):
        precision = len(trading_size_str) - trading_size_str.index('.') - 1
    else:
        precision = 0
    format = Decimal('0.' + precision * '0')
    print(float(Decimal('0.124535345').quantize(format)))


if __name__ == '__main__':
    run = AbstractTradeRun({})
    position = SymbolPosition(1, 'testw', Decimal(120), Decimal(11), Decimal(10))
    run.record_position(position)
    positions = run.query_position(['testw'], 0, 100000)
    print(positions)

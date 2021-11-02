from decimal import Decimal


class SymbolPosition(object):
    def __init__(self, timestamp: int, symbol: str,
                 amount: Decimal, entry_price: Decimal, price: Decimal):
        self.timestamp = timestamp
        self.symbol = symbol
        self.amount = amount
        self.entry_price = entry_price
        self.price = price

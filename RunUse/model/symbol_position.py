class SymbolPosition(object):
    def __init__(self, timestamp: int, symbol: str,
                 amount: float, entry_price: float, price: float):
        self.timestamp = timestamp
        self.symbol = symbol
        self.amount = amount
        self.entry_price = entry_price
        self.price = price

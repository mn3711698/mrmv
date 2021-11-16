class SymbolPosition(object):
    def __init__(self, timestamp: int = None, symbol: str = None,
                 amount: float = None, entry_price: float = None, price: float = None):
        self.timestamp = timestamp
        self.symbol = symbol
        self.amount = amount
        self.entry_price = entry_price
        self.price = price

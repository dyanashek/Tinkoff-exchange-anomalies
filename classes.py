# a class that contains main information about share
class Share:
    def __init__(self, name, ticker, figi, lot=0, currency='', candles=False, sigma=0, average=0, price_delta=0):
        self.name = name
        self.ticker = ticker
        self.figi = figi
        self.lot = lot
        self.currency = currency
        self.candles = candles
        self.sigma = sigma
        self.average = average
        self.price_delta = price_delta

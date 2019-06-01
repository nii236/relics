"""
_talib.py

"""

import numpy as np
import talib
import datetime
import strategy
import goxapi
# import _bfx
import time
# from _bfx import Bitfinex
from goxapi import OHLCV

class Strategy(strategy.Strategy):
    """a TA bot"""
    def __init__(self, gox):
        strategy.Strategy.__init__(self, gox)
    def slot_keypress(self, gox, (key)):
        """a key has been pressed"""

        if key == ord("c"):
            # cancel existing rebalancing orders and suspend trading
            self.debug("canceling all rebalancing orders")
            
    def slot_history_changed(self, history, _dummy):
        """History has changed so recalculate EMAs"""
        candles = []

        # read them all - don't wory about the history parameter
        for c in reversed(self.gox.history.candles):
            candles.append(
                OHLCV(
                                    c.tim,
                    # adjust values to be human readable
                    goxapi.int2float(c.opn, self.gox.currency),
                    goxapi.int2float(c.hig, self.gox.currency),
                    goxapi.int2float(c.low, self.gox.currency),
                    goxapi.int2float(c.cls, self.gox.currency),
                    goxapi.int2float(c.vol, "BTC")
                )
            )

        self.debug("New EMAs from history with %d candles" % len(candles))

        rng = range(len(candles))
        iterable = (candles[i].opn for i in rng)
        a_opn = np.fromiter(iterable, np.float)

        iterable = (candles[i].hig for i in rng)
        a_hig = np.fromiter(iterable, np.float)

        iterable = (candles[i].low for i in rng)
        a_low = np.fromiter(iterable, np.float)

        iterable = (candles[i].cls for i in rng)
        a_cls = np.fromiter(iterable, np.float)

        iterable = (candles[i].vol for i in rng)
        a_vol = np.fromiter(iterable, np.float)

        a_sema = talib.EMA(a_cls, 20)
        a_lema = talib.EMA(a_cls, 44)
        a_gcr = (a_sema[-1] - a_lema[-1])/a_lema[-1]*100
		
        # Current price in relation to EMA
        self.debug("Short Exp Moving Average (30 Samples) = %f" % a_sema[-1])
        self.debug("Long Exp Moving Average (86 Samples) = %f" % a_lema[-1])
        self.debug("Goomboo's cross = %f pc" % a_gcr)

        target = open('trade', 'w')
        if a_gcr < 0: line = time.strftime("%H:%M:%S") + ": Sell"
    	if a_gcr > 0: line = time.strftime("%H:%M:%S") + ": Buy"
        target.write(line)
        target.close()
        
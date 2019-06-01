"""
_bfx.py

Bitfinex Implementation with EMA crossover automatic shorting longing

SUPER ALPHA 0.0000001

"""
from decimal import Decimal
import requests
import json
import base64
import hmac
import hashlib
import time
import types

import numpy as np
import talib
import datetime
import strategy
import goxapi
from goxapi import OHLCV

BFXKEY = 'EXAMPLE'
BFXSECRET = 'EXAMPLE'

BITFINEX = 'api.bitfinex.com/'
DECIMAL_KEYS = set(['amount', 'ask', 'available', 'bid', 'executed_amount', 'high', 'last_price', 'low', 'mid', 'original_amount', 'price', 'remaining_amount', 'timestamp', 'volume'])
TRADE_AMOUNT = "1"
# CURRENT_POSITION = "NA"

class Strategy(strategy.Strategy):
    """a bot which uses EMA crossing over to margin trade on BitFinex"""
    def __init__(self, gox):
        strategy.Strategy.__init__(self, gox)
        self.CURRENT_POSITION = "NA"
        self.marketBFX = Bitfinex()
        self.marketBFX.key = BFXKEY
        self.marketBFX.secret = BFXSECRET 
        self.a_gcr = 0
        self.BOT_ACTIVE = False

    def slot_keypress(self, gox, (key)):
        marketBFX = Bitfinex()
        marketBFX.key = BFXKEY
        marketBFX.secret = BFXSECRET 
        if key == ord("i"):
            self.debug("GETTING TICKER")
            tick = marketBFX.ticker()
            self.debug(tick[u'last_price'])
        if key == ord("t"):
            self.debug("GETTING CURRENT POSITION TARGET")
            self.debug(self.CURRENT_POSITION)
        if key == ord("b"):
            self.debug("CHECKING BALANCES")
            balance = marketBFX.balances()
            self.debug(balance[0][u'available'], "BTC")
        # if key == ord("z"):
            # self.debug("GOING SHORT")
            # tick = marketBFX.ticker()
            # payload = {}
            # payload["symbol"]     = "btcusd"
            # payload["amount"]     = TRADE_AMOUNT
            # payload["price"]      = tick[u'ask']
            # payload["exchange"]   = "all"
            # payload["side"]       = "sell"
            # payload["type"]       = "limit"
            # response = marketBFX.order_new(payload)
            # self.debug("...DONE")
        # if key == ord("a"):
            # self.debug("GOING LONG")
            # tick = marketBFX.ticker()
            # payload = {}
            # payload["symbol"]     = "btcusd"
            # payload["amount"]     = TRADE_AMOUNT
            # payload["price"]      = tick[u'bid']
            # payload["exchange"]   = "all"
            # payload["side"]       = "buy"
            # payload["type"]       = "limit"
            # response = marketBFX.order_new(payload)
            # self.debug("...DONE")
        if key == ord("s"):
            if not self.BOT_ACTIVE:
                self.debug("BOT STARTING")
                self.BOT_ACTIVE = True
                self.debug("...DONE")
            else:
                self.debug("BOT STOPPING")
                self.BOT_ACTIVE = False
                self.debug("...DONE")
        if key == ord("c"):
            self.debug("CANCELLING EARLIEST ORDER")
            payload = {}
            orders = marketBFX.orders()
            if len(orders) > 0:
                payload["order_id"]= orders[0][u'id']
                response = marketBFX.order_cancel(payload)
            self.debug("...DONE")
        if key == ord("v"):
            self.debug("CANCELLING ALL ORDERS AND POSITIONS")
            payload = {}
            list = []
            orders = marketBFX.orders()
            positions = marketBFX.positions()
            i = 0
            while i < len(orders):
                list.append(orders[i][u'id'])
                i+=1
            j = 0
            while j < len(positions):
                list.append(positions[i][u'id'])
                j+=1
            payload["order_ids"] = list
            response = marketBFX.orders_cancel_multiple(payload)
            # self.debug(payload)
            # self.debug(response)
            self.debug("...DONE")
        if key == ord("o"):
            self.debug("GETTING ACTIVE ORDERS")
            orders = marketBFX.orders()
            self.debug(len(orders))
            # self.debug(orders)
        if key == ord("p"):
            self.debug("GETTING ACTIVE POSITIONS")
            positions = marketBFX.positions()
            self.debug(positions)
        if key == ord("m"):
            self.debug("GETTING PROFIT/LOSS")
            positions = marketBFX.positions()
            if len(positions)>0: self.debug(positions[0][u'pl'])
            else: self.debug("0")
        if key == ord("g"):
            self.debug("Goomboo's cross = %f pc" % self.a_gcr)
    def cancel_all(self):
        payload = {}
        list = []
        orders = self.marketBFX.orders()
        positions = self.marketBFX.positions()
        i = 0
        while i < len(orders):
            list.append(orders[i][u'id'])
            i+=1
        j = 0
        while k < len(positions):
            list.append(positions[i][u'id'])
            j+=1
        payload["order_ids"] = list
        response = self.marketBFX.orders_cancel_multiple(payload)
    def go_short(self):
        #Make sure no active orders or positions
        orders = self.marketBFX.orders()
        positions = self.marketBFX.positions()
        if len(orders) > 0 and len(positions) > 0:
            cancel_all()
        self.debug("GOING SHORT")
        tick = self.marketBFX.ticker()
        payload = {}
        payload["symbol"]     = "btcusd"
        payload["amount"]     = TRADE_AMOUNT
        payload["price"]      = tick[u'ask']
        payload["exchange"]   = "all"
        payload["side"]       = "sell"
        payload["type"]       = "limit"
        response = self.marketBFX.order_new(payload)
        self.debug("...DONE")

    def go_long(self):
        orders = self.marketBFX.orders()
        positions = self.marketBFX.positions()
        if len(orders) > 0 and len(positions) > 0:
            cancel_all()
        self.debug("GOING LONG")
        tick = self.marketBFX.ticker()
        payload = {}
        payload["symbol"]     = "btcusd"
        payload["amount"]     = TRADE_AMOUNT
        payload["price"]      = tick[u'bid']
        payload["exchange"]   = "all"
        payload["side"]       = "buy"
        payload["type"]       = "limit"
        response = self.marketBFX.order_new(payload)
        self.debug("...DONE")
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

        # self.debug("New EMAs from history with %d candles" % len(candles))

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

        a_sema = talib.EMA(a_cls, 40)
        a_lema = talib.EMA(a_cls, 88)
        a_gcr = (a_sema[-1] - a_lema[-1])/a_lema[-1]*100
        self.a_gcr = a_gcr
        # Current price in relation to EMA
        # self.debug("Short Exp Moving Average (20 Samples) = %f" % a_sema[-1])
        # self.debug("Long Exp Moving Average (44 Samples) = %f" % a_lema[-1])
        # self.debug("Goomboo's cross = %f pc" % a_gcr)

        target = open('trade', 'w')
        line = "BEGIN"
        if a_gcr < 0: 
            line = time.strftime("%H:%M:%S") + ": Sell"
    	if a_gcr > 0: 
            line = time.strftime("%H:%M:%S") + ": Buy"
        target.write(line)
        target.close()

        if (self.CURRENT_POSITION == "SELL" or self.CURRENT_POSITION == "NA") and a_gcr > 0.25 and self.BOT_ACTIVE:
            # self.go_long()
            self.CURRENT_POSITION = "BUY"
        if (self.CURRENT_POSITION == "BUY" or self.CURRENT_POSITION == "NA") and a_gcr < -0.25 and self.BOT_ACTIVE:
            # self.go_short()
            self.CURRENT_POSITION = "SELL"
def decimalize(obj, keys):
    if isinstance(obj, types.ListType):
        return [decimalize(xs, keys) for xs in obj]
    if not isinstance(obj, types.DictType):
        return obj
    #print obj
    def to_decimal(k, val):
        if val == None:
            return None
        if isinstance(val, types.ListType):
            return [decimalize(ys, keys) for ys in val]
        if k in keys:
            return Decimal(val)
        return val
    return { k: to_decimal(k, obj[k]) for k in obj }


def undecimalize(obj):
    if isinstance(obj, types.ListType):
        return map(undecimalize, obj)
    if not isinstance(obj, types.DictType):
        return obj
    #print obj
    def from_decimal(val):
        if isinstance(val, Decimal):
            return str(val)
        return val
    return { k: from_decimal(obj[k]) for k in obj }


class Bitfinex(object):
    def ticker(self, symbol="btcusd"):
        r = requests.get("https://"+BITFINEX+"/v1/ticker/"+symbol, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def today(self, symbol="btcusd"):
        r = requests.get("https://"+BITFINEX+"/v1/today/"+symbol, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)
	
    def candles(self, symbol="btcusd"):
        r = requests.get("https://"+BITFINEX+"/v1/candles/"+symbol, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)
	
    def book(self, payload, symbol="btcusd"):
        headers = self._prepare_payload(False, payload)
        r = requests.get("https://"+BITFINEX+"/v1/book/"+symbol, headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def trades(self, payload, symbol="btcusd"):
        headers = self._prepare_payload(False, payload)
        r = requests.get("https://"+BITFINEX+"/v1/trades/"+symbol, headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def symbols(self):
        r = requests.get("https://"+BITFINEX+"/v1/symbols", verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def order_new(self, payload):
        payload["request"] = "/v1/order/new"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.post("https://"+BITFINEX+"/v1/order/new", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def order_cancel(self, payload):
        payload["request"] = "/v1/order/cancel"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.post("https://"+BITFINEX+"/v1/order/cancel", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)

    def orders_cancel_multiple(self, payload):
        payload["request"] = "/v1/order/cancel/multi"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.post("https://"+BITFINEX+"/v1/order/cancel/multi", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)

    def order_status(self, payload):
        payload["request"] = "/v1/order/status"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.get("https://"+BITFINEX+"/v1/order/status", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)


    def orders(self):
        payload = {}
        payload["request"] = "/v1/orders"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.get("https://"+BITFINEX+"/v1/orders", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)

    def positions(self):
        payload = {}
        payload["request"] = "/v1/positions"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.get("https://"+BITFINEX+"/v1/positions", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)

    def balances(self):
        payload = {}
        payload["request"] = "/v1/balances"
        payload["nonce"] = str(long(time.time() * 100000))
        headers = self._prepare_payload(True, payload)
        r = requests.get("https://"+BITFINEX+"/v1/balances", headers=headers, verify=False)
        return decimalize(r.json(), DECIMAL_KEYS)




    # Private
    def _prepare_payload(self, should_sign, d):
        j = json.dumps(undecimalize(d))
        data = base64.standard_b64encode(j)


        if should_sign:
            h = hmac.new(self.secret, data, hashlib.sha384)
            signature = h.hexdigest()


            return {
                "X-BFX-APIKEY": self.key,
                "X-BFX-SIGNATURE": signature,
                "X-BFX-PAYLOAD": data,
            }
        else:
            return {
                "X-BFX-PAYLOAD": data,
            }
        
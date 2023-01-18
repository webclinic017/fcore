import unittest

import sys
sys.path.append('../')

import yfinance
import pandas as pd

from datetime import datetime, timedelta

from mockito import when, verify, unstub

from data.fvalues import Timespans
from data import yf
from data.fdata import FdataError

class History():
    def history(self, interval, start, end):
        pass

class Test(unittest.TestCase):
    def tearDown(self):
        unstub()

    def test_0_check_arg_parser(self):
        query = yf.YFQuery()
        query.symbol = 'SPY'

        last_date = datetime.now()
        first_date = last_date - timedelta(days=7)
        timespan = Timespans.Day

        query.first_date = first_date
        query.last_date = last_date
        query.timespan = timespan

        yf_obj = yf.YF(query)

        hist = History()

        quotes_data = [{'v': 11, 'o': 1, 'c': 3, 'h': 5, 'l': 7, 'cl': 'NULL', 'n': 'NULL', 'vw': 'NULL', 'd': 9, 't': query.first_date_ts}, \
                       {'v': 12, 'o': 2, 'c': 4, 'h': 6, 'l': 8, 'cl': 'NULL', 'n': 'NULL', 'vw': 'NULL', 'd': 10, 't': query.last_date_ts}]

        df = pd.DataFrame({'Date': [first_date, last_date],
                           'Open': [1, 2],
                           'Close': [3, 4],
                           'High': [5, 6],
                           'Low': [7, 8],
                           'Dividends': [9, 10],
                           'Volume': [11, 12]
                         })
        df = df.set_index('Date')

        # Mocking
        when(yfinance).Ticker(query.symbol).thenReturn(hist)
        when(hist).history(interval=query.get_timespan(), \
                           start=query.first_date_str, \
                           end=query.last_date_str).thenReturn(df)

        return_data = yf_obj.fetch_quotes()

        verify(yfinance, times=1).Ticker(query.symbol)
        verify(hist, times=1).history(interval=query.get_timespan(), \
                                      start=query.first_date_str, \
                                      end=query.last_date_str)

        assert return_data == quotes_data

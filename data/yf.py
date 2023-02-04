"""Yahoo Finance wrapper.

The author is Zmicier Gotowka

Distributed under Fcore License 1.0 (see license.md)
"""
from datetime import datetime
import pytz

import yfinance as yfin

from data import fdata
from data.fvalues import Timespans, def_first_date, def_last_date
from data.fdata import FdataError

class YF(fdata.BaseFetchData):
    """
        Yahoo Finance wrapper class.
    """
    def __init__(self, **kwargs):
        """
            Initialize Yahoo Finance wrapper class.
        """
        super().__init__(**kwargs)

        # Default values
        self.source_title = "YF"

    def get_timespan(self):
        """
            Get the timespan for queries.

            Raises:
                FdataError: incorrect/unsupported timespan requested.

            Returns:
                str: timespan for YF query.
        """
        if self.timespan == Timespans.Minute:
            return '1m'
        elif self.timespan == Timespans.TwoMinutes:
            return '2m'
        elif self.timespan == Timespans.FiveMinutes:
            return '5m'
        elif self.timespan == Timespans.FifteenMinutes:
            return '15m'
        elif self.timespan == Timespans.ThirtyMinutes:
            return '30m'
        elif self.timespan == Timespans.Hour:
            return '1h'
        elif self.timespan == Timespans.NinetyMinutes:
            return '90m'
        elif self.timespan == Timespans.Day:
            return '1d'
        elif self.timespan == Timespans.FiveDays:
            return '5d'
        elif self.timespan == Timespans.Week:
            return "1wk"
        elif self.timespan == Timespans.Month:
            return '1mo'
        elif self.timespan == Timespans.Quarter:
            return '3mo'
        else:
            raise FdataError(f"Requested timespan is not supported by Polygon: {self.timespan}")

    def fetch_quotes(self):
        """
            The method to fetch quotes.

            Returns:
                list: quotes data

            Raises:
                FdataError: network error, no data obtained, can't parse json or the date is incorrect.
        """
        if self.first_date_ts != def_first_date or self.last_date_ts != def_last_date:
            data = yfin.Ticker(self.symbol).history(interval=self.get_timespan(),
                                                        start=self.first_date_str,
                                                        end=self.last_date_str)
        else:
            data = yfin.Ticker(self.symbol).history(interval=self.get_timespan(), period='max')

        length = len(data)

        if length == 0:
            raise FdataError(f"Can not fetch quotes for {self.symbol}. No quotes fetched.")

        # Create a list of dictionaries with quotes
        quotes_data = []

        for ind in range(length):
            dt = data.index[ind]
            dt = dt.replace(tzinfo=pytz.utc)
            ts = int(datetime.timestamp(dt))

            if self.get_timespan() in [Timespans.Day, Timespans.Week, Timespans.Month]:
                # Add 23:59:59 to non-intraday quotes
                quote_dict['t'] = ts + 86399

            quote_dict = {
                "v": data['Volume'][ind],
                "o": data['Open'][ind],
                "c": data['Close'][ind],
                "h": data['High'][ind],
                "l": data['Low'][ind],
                "cl": "NULL",
                "n": "NULL",
                "vw": "NULL",
                "d": data['Dividends'][ind],
                "t": ts
            }

            quotes_data.append(quote_dict)

        if len(quotes_data) != length:
            raise FdataError(f"Obtained and parsed data length does not match: {length} != {len(quotes_data)}.")

        return quotes_data

    def get_rt_data(self, to_cache=False):
        """
            Get real time data. Used in screening.

            Args:
                to_cache(bool): indicates if real time data should be cached in a database.

            Returns:
                list: real time data.
        """
        data = yfin.download(tickers=self.symbol, period='1d', interval='1m')
        row = data.iloc[-1]

        result = [self.symbol,
                  None,
                  self.source_title,
                  # TODO check if such datetime manipulations may have an impact depending on a locale.
                  str(data.index[-1])[:16],
                  self.timespan.value,
                  row['Open'],
                  row['High'],
                  row['Low'],
                  row['Close'],
                  row['Adj Close'],
                  row['Volume'],
                  None,
                  None,
                  None]

        # TODO caching should be implemented

        return result

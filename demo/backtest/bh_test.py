"""Demonstration of Buy and Hold strategy backtesting.

The author is Zmicier Gotowka

Distributed under Fcore License 1.0 (see license.md)
"""

from backtest.bh import BuyAndHold

from backtest.base import BackTestError
from backtest.stock import StockData

from data.futils import standard_chart

from data.futils import write_image
from data.fdata import FdataError

from data.yf import YFError, YFQuery, YF

import sys

threshold = 500  # Quotes num threshold for the test

if __name__ == "__main__":
    # Get quotes
    try:
        # Fetch quotes if there are less than a threshold number of records in the database for the specified timespan.
        query = YFQuery(symbol="SPY", first_date="2020-10-01", last_date="2022-11-1")
        rows, num = YF(query).fetch_if_none(threshold)
    except (YFError, FdataError) as e:
        print(e)
        sys.exit(2)

    length = len(rows)

    if num > 0:
        print(f"Fetched {num} quotes for {query.symbol}. Total number of quotes used is {length}.")
    else:
        print(f"No need to fetch quotes for {query.symbol}. There are {length} quotes in the database and it is >= the threshold level of {threshold}.")

    quotes = StockData(rows=rows,
                          title=query.symbol,
                          spread=0.1,
                          use_yield=1.5,
                          yield_interval=90
                         )

    bh = BuyAndHold(
        data=[quotes],
        commission=2.5,
        periodic_deposit=500,
        deposit_interval=30,
        inflation=2.5,
        initial_deposit=10000
    )

    try:
        bh.calculate()
    except BackTestError as e:
        print(f"Can't perform backtesting calculation: {e}")
        sys.exit(2)

    results = bh.get_results()

    ##################
    # Build the charts
    ##################

    fig = standard_chart(results, title=f"BuyAndHold Example Testing for {query.symbol}")

    ######################
    # Write the chart
    ######################

    new_file = write_image(fig)

    print(f"{new_file} is written.")
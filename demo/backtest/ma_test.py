"""Demonstration of MA/price cross strategy backtesting.

The author is Zmicier Gotowka

Distributed under Fcore License 1.0 (see license.md)
"""

from backtest.ma import MA

from backtest.base import BackTestError
from backtest.stock import StockData

from backtest.bh import BuyAndHold

from data.futils import standard_margin_chart

import plotly.graph_objects as go

from data.futils import write_image
from data.fdata import FdataError

from data.yf import YFError, YFQuery, YF

import sys

period = 50  # Period used in strategy
threshold = 1385  # Quotes num threshold for the test

if __name__ == "__main__":
    # Get quotes
    try:
        # Fetch quotes if there are less than a threshold number of records in the database for the specified timespan.
        query = YFQuery(symbol="SPY", first_date="2017-01-30", last_date="2022-8-1")
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
                          margin_rec=0.4,
                          margin_req=0.7,
                          spread=0.1,
                          margin_fee=1,
                          trend_change_period=2,
                          trend_change_percent=2
                         )

    ma = MA(
        data=[quotes],
        commission=2.5,
        initial_deposit=10000,
        periodic_deposit=500,
        deposit_interval=30,
        inflation=2.5,
        period=period,
        margin_rec=0.9,
        margin_req=1,
    )

    # Buy and Hold to compare

    quotes_bh = StockData(rows=rows,
                             title=query.symbol,
                             spread=0.1,
                            )

    bh = BuyAndHold(
        data=[quotes_bh],
        commission=2.5,
        initial_deposit=10000,
        periodic_deposit=500,
        deposit_interval=30,
        inflation=2.5,
        offset=period
    )

    try:
        ma.calculate()
        bh.calculate()
    except BackTestError as e:
        print(f"Can't perform backtesting calculation: {e}")
        sys.exit(2)

    results_bh = bh.get_results()
    results = ma.get_results()

    ##################
    # Build the charts
    ##################

    fig = standard_margin_chart(results, title=f"MA/Quote Cross Backtesting Example for {query.symbol}")

    # Append MA values to the main chart
    fig.add_trace(go.Scatter(x=results.DateTime, y=results.Symbols[0].Tech[0], mode='lines', name="MA"), secondary_y=False)

    # Append B&H comparison to the second subchart
    fig.add_trace(go.Scatter(x=results.DateTime, y=results_bh.TotalValue, mode='lines', name="Total Value Buy and Hold", line=dict(color="#32CD32")), row=2, col=1)

    ######################
    # Write the chart
    ######################

    new_file = write_image(fig)

    print(f"{new_file} is written.")
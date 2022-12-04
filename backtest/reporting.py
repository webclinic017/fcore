"""Module with reporting classes.

The author is Zmicier Gotowka

Distributed under Fcore License 1.0 (see license.md)
"""

import plotly.graph_objects as go
from plotly import subplots

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from enum import IntEnum

import numpy as np

import copy
import io
import os
import subprocess
import platform
import glob

from matplotlib import font_manager

from math import ceil

class ChartType(IntEnum):
    Line = 0
    Candle = 1
    Ohlc = 2

class ReportsError(Exception):
    """Exception class for reporting."""

class Report():
    """The reporting class."""
    def __init__(self, data, width, margin=False, color="LightSteelBlue"):
        """Initializes the instance of reporting class.
        
            Args:
                margin(bool): indicates if margin related data should be used.
                data(BTData): the main data to use. Used if no other dataset is provided in further functions.
                width(int): the width of the chart.
                color(str): the color of chart's background.
        """

        # Generate margin-related data
        self._margin = margin

        # The width of the chart
        if width <= 0:
            raise ReportsError(f"Invalid width specified: {width}. The width should be > 0.")
        self._width = width

        # The container for subcharts. Standalone charts are preferred than plotly subcharts. 
        self._charts = []

        # The container for annotations
        self._annotations = []

        # The default dataset
        self._data = data

        # The color of chart's background
        self._color = color

        # The default dimensions of an annotation
        self._annotation_height = 170
        self._annotation_width = 1000

    def adjust_trades(self, data=None):
        """
            Set trade related data to None if there was no trades this day.
            It may be used in some charting.

            Args:
                data(BTData): instance with backtesting results.
        """
        if data is None:
            data = self._data

        alt_data = copy.deepcopy(data)
        for i in range(len(data.Symbols)):
            for j in range(len(data.TotalTrades)):
                price_long = data.Symbols[i].TradePriceLong[j]
                price_short = data.Symbols[i].TradePriceShort[j]
                price_margin = data.Symbols[i].TradePriceMargin[j]

                if np.isnan(price_long) and np.isnan(price_short) and np.isnan(price_margin):
                    alt_data.Symbols[i].TradesNo = (j, None)
                    alt_data.TotalTrades = (j, None)

        return alt_data

    def get_charts_num(self, fig):
        """
            Get the number of subcharts in the fugure.

            Args:
                fig(go.Figure): figure to get the number of subcharts.

            Returns:
                int: the number of subcharts in the figure.
        """
        num = 0

        for keyword in fig.layout:
            if keyword.startswith('xaxis'):
                num += 1

        return num

    def update_layout(self, fig, title, height=600):
        """
            Update layout for a chart.

            Args:
                fig(go.Figure): figure to update the layout.
                title(str): title of the chart.
                height(int): height of each subchart (if any).
        """
        # Top offset depends on if we have a chart title (which requires more space)
        top = 70
        if title is None:
            top = 30

        fig.update_layout(
            title_text=title,
            autosize=False,
            width=self._width,
            height=height * self.get_charts_num(fig),
            legend_x=0,
            margin=dict(
                l=50,
                r=50,
                b=0,
                t=top,
                pad=4,
            ),
            legend=dict(
                bordercolor="Black",
                borderwidth=2
            ),
            paper_bgcolor=self._color)

    def add_quotes_chart(self, data=None, index=0, title=None, chart_type=ChartType.Line, fig=None, height=600):
        """Add a quotes chart with price, trades and dates/time to the chart list.
        
            Args:
                data(BtData): data to build the chart.
                index(int): symbol's index to build the chart.
                title(str): the title of the chart.
                chart_type(ChartType): chart type (line, candle, bar)
                fig(go.figure): custom figure to use.
                height(int): the height of the chart image.

            Returns:
                go.figure: created figure.
        """
        if data is None:
            data = self._data

        # The symbol to use
        symbol = data.Symbols[index]

        if fig is None:
            # Create the default figure
            fig = subplots.make_subplots(subplot_titles=[symbol.Title])

        if chart_type == ChartType.Line:
            fig.add_trace(go.Scatter(x=data.DateTime,
                                     y=symbol.Close,
                                     mode='lines',
                                     name='Quotes'))
        elif chart_type == ChartType.Candle:
            fig.add_trace(go.Candlestick(x=data.DateTime,
                                         open=symbol.Open,
                                         close=symbol.Close,
                                         high=symbol.High,
                                         low=symbol.Low,
                                         name='Quotes'))
            
            fig.update_layout(xaxis_rangeslider_visible=False)
        elif chart_type == ChartType.Ohlc:
            fig.add_trace(go.Ohlc(x=data.DateTime,
                                  open=symbol.Open,
                                  close=symbol.Close,
                                  high=symbol.High,
                                  low=symbol.Low,
                                  name='Quotes'))

            fig.update_layout(xaxis_rangeslider_visible=False)

        fig.add_trace(go.Scatter(x=data.DateTime,
                                 y=symbol.TradePriceLong,
                                 mode='markers',
                                 marker=dict(color='orange'),
                      name='Trades'))

        if self._margin is True:
            fig.add_trace(go.Scatter(x=data.DateTime,
                                     y=symbol.TradePriceShort,
                                     mode='markers',
                                     marker=dict(color='brown'),
                          name='Short Trades'))

            fig.add_trace(go.Scatter(x=data.DateTime,
                                        y=symbol.TradePriceMargin,
                                        mode='markers',
                                        name='Margin Req Trades'))

        self.update_layout(fig=fig, title=title, height=height)

        # Workaround to handle plotly whitespace issue when adding markers
        fig.update_layout(xaxis={"range":[data.DateTime[0], data.DateTime[-1]]})

        self._charts.append(fig)

        return fig

    def add_expenses_chart(self, data=None, title=None, fig=None, height=600):
        """Add an expenses chart to the charts list.
        
            Args:
                data(BtData): data to build the chart.
                title(str): the title of the chart.
                fig(go.figure): custom figure to use.
                height(int): the height of the chart image.

            Returns:
                go.figure: created figure.
        """
        if data is None:
            data = self._data

        if fig is None:
            # Create the default figure
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=data.DateTime, y=data.TotalExpenses, mode='lines', name="Expenses"))
            fig.add_trace(go.Scatter(x=data.DateTime, y=data.CommissionExpense, mode='lines', name="Commission"))
            fig.add_trace(go.Scatter(x=data.DateTime, y=data.SpreadExpense, mode='lines', name="Spread"))

            if self._margin is True:
                fig.add_trace(go.Scatter(x=data.DateTime, y=data.DebtExpense, mode='lines', name="Margin Expenses"))
                fig.add_trace(go.Scatter(x=data.DateTime, y=data.OtherExpense, mode='lines', name="Yield Expenses"))

        self.update_layout(fig=fig, title=title, height=height)
        self._charts.append(fig)

        return fig

    def add_portfolio_chart(self, data=None, title=None, fig=None, height=600):
        """Add a chart with portfolio performance.
        
            Args:
                data(BtData): data to build the chart.
                title(str): the title of the chart.
                fig(go.figure): custom figure to use.
                height(int): the height of the chart image.

            Returns:
                go.figure: created figure.
        """
        if data is None:
            data = self._data

        if fig is None:
            # Create the default figure
            fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.DateTime, y=data.TotalValue, mode='lines', name="Total Value"))
        fig.add_trace(go.Scatter(x=data.DateTime, y=data.Deposits, mode='lines', name="Deposits"))
        fig.add_trace(go.Scatter(x=data.DateTime, y=data.OtherProfit, mode='lines', name="Dividends"))

        self.update_layout(fig=fig, title=title, height=height)
        self._charts.append(fig)

        return fig

    def add_trades_chart(self, data=None, title=None, fig=None, height=600):
        """
            Add a chart with trades statistics.

            Args:
                data(BtData): data to build the chart.
                title(str): the title of the chart.
                fig(go.figure): custom figure to use.
                height(int): the height of the chart image.

            Returns:
                go.figure: created figure.
        """
        if data is None:
            data = self._data

        if fig is None:
            # Create the default figure
            fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.DateTime, y=data.TotalTrades, mode='lines', name="Total Trades"))

        # Iterate through all charts to get trades statistics
        for symbol in data.Symbols:
            fig.add_trace(go.Scatter(x=data.DateTime, y=symbol.TradesNo, mode='lines', name=f"{symbol.Title} Trades"))

        self.update_layout(fig=fig, title=title, height=height)
        self._charts.append(fig)

        return fig

    def add_custom_chart(self, fig, title=None, height=600):
        """
            Add custom chart to the charts list.

            Args:
                fig(go.figure): the custom chart
                title(str): title of the custom chart
                height(int): the height of the custom chart
        """
        self.update_layout(fig=fig, title=title, height=height)
        self._charts.append(fig)

        return fig

    def add_annotations(self, data=None, title=None, margin=None):
        """
            Add annotation with strategy results to the chart.

            Args:
                data(BtData): data to calculate the results.
                title(str): the title of the strategy.
                margin(bool): indicates if the strategy involves margin.

            Returns:
                str: The annotation in string form.
        """
        if data is None:
            data = self._data

        if margin is None:
            margin = self._margin

        # Create image for the annotations.
        result = Image.new('RGB', (self._width, self._annotation_height), color=self._color)

        # Prepare the annotations
        invested = data.Deposits[-1]
        final_value = data.TotalValue[-1]
        profit = final_value / invested * 100 - 100

        performance = f"Invested:     {round(invested, 2)}\n"\
                      f"Total value:  {round(final_value, 2)}\n"\
                      f"Profit:       {round(profit, 2)}%\n"\
                      f"Yield profit: {round(data.OtherProfit[-1], 2)}\n"\
                      f"Total trades: {data.TotalTrades[-1]}"\


        expenses = f"Total expenses:     {round(data.TotalExpenses[-1], 2)}\n"\
                   f"Commission expense: {round(data.CommissionExpense[-1], 2)}\n"\
                   f"Spread expense:     {round(data.SpreadExpense[-1], 2)}\n"\
                   f"Debt expense:       {round(data.DebtExpense[-1], 2)}\n"\
                   f"Yield expense:      {round(data.OtherExpense[-1], 2)}"\

        # Put annotations to the image
        draw = ImageDraw.Draw(result)

        # Find the font to use on each platform
        font_type = font_manager.FontProperties(family='monospace', weight='regular')
        path = font_manager.findfont(font_type)
        font = ImageFont.truetype(path, 22)
        
        y_offset = 15

        if title != None:
            bold_font_type = font_manager.FontProperties(family='monospace', weight='bold')
            bold_path = font_manager.findfont(bold_font_type)
            bold_font = ImageFont.truetype(bold_path, 22)

            draw.text((50, 5), title, (54, 69, 79), font=bold_font)
            y_offset = 35

        draw.text((50, y_offset), performance, (54, 69, 79), font=font)
        draw.text((500, y_offset), expenses, (54, 69, 79), font=font)

        self._annotations.append(result)

    def combine_charts(self):
        """
            Get the combined byteimage (PNG) of all charts.
            The custom mechanism of combining charts is preferred over plotly subcharts because it looks better and more flexible.

            Raises:
                ReportsError: no charts are generated yet.

            Returns:
                byteimage(PNG): the combined byte image of all charts.
        """
        if len(self._charts) == 0:
            raise ReportsError("No charts are generated yet.")

        # Get the width of the resulting image
        width = self._charts[0].layout.width

        images = []
        height = 0

        # Iterate through all the charts to get byteimages and calculate sizes
        for fig in self._charts:
            images.append(fig.to_image(format="png"))
            height += fig.layout.height

        # Add height of annotations
        img_per_row = int(self._width / self._annotation_width)
        annotations_height = ceil(len(self._annotations) / img_per_row) * self._annotation_height

        height += int(annotations_height)

        # Create the resulting image
        result = Image.new('RGB', (width, height))

        # The variable to store the current vertical image position
        y = 0

        # Iterate through images to append them one after another
        for image in images:
            img = Image.open(io.BytesIO(image))
            result.paste(img, (0, y))
            y += img.height

        # The variable to store the current horizontal position
        x = 0

        # Iterate through annotations images to append them one after another
        for annotation in self._annotations:
            result.paste(annotation, (x, y))

            x += self._annotation_width

            if x > (self._width - self._annotation_width):
                x = 0 
                y += self._annotation_height

        return result

    def write_image(self, image=None):
        """
            Write plotly figure to a disk.

            Args:
                image(PIL.image): image to write.

            Returns:
                str: new file path.

            Raises:
                RuntimeError: can't generate a filename.
        """
        if image is None:
            image = self.combine_charts()

        img_dir = "images/"

        if os.path.exists(img_dir) == False:
            os.mkdir(img_dir)

        files = glob.glob(img_dir + "fig_*.png")

        files.sort(key=lambda x: int(x.partition('_')[2].partition('.')[0]))

        if len(files) == 0:
            last_file = 0
        else:
            last_file = files[-1]
            last_file = last_file.replace('.png', '').replace(img_dir + 'fig_', '')
        
        try:
            new_counter = int(last_file) + 1
        except ValueError as e:
            raise RuntimeError(f"Can't generate new filename. {last_file} has a broken filename pattern.") from e

        new_file = img_dir + "fig_" + f"{new_counter}" + ".png"

        image.save(new_file,"PNG")

        return new_file

    def show_image(self, image_path=None):
        """
            Write the image (if no path is specified) and open it in the system default image viewer.

            Args:
                image_path(str): path to image to show.

            Returns:
                str: path to the image
        """
        if image_path is None:
            image_path = self.write_image()

        # Open image file in the default viewer.
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', image_path))
        elif platform.system() == 'Windows':
            os.startfile(image_path)
        else:  # Linux
            subprocess.call(('xdg-open', image_path))

        return image_path
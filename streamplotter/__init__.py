import collections
import itertools
import japanize_matplotlib
import math
import matplotlib.animation
import matplotlib.figure
import matplotlib.lines
import matplotlib.pyplot
import numpy
import sys
import threading
import time
import uuid


class DataStream:

    def __init__(self, initial: float = 0, interval: int = 1):
        self.interval = interval
        self.stack = collections.deque()
        self.reserved = collections.deque()
        self.reserved.append(initial)
        self.lock = threading.Lock()
        thread = threading.Thread(target=self.update, daemon=True)
        thread.start()

    def update(self):
        basetime = time.time()
        while True:
            value = self.reserved.popleft() if len(self.reserved) > 0 else None
            self.stack.append(value)
            elapsed = time.time() - basetime
            seconds = elapsed + (self.interval - elapsed % self.interval)
            basetime += seconds
            while time.time() < basetime:
                time.sleep(0.1)

    def append(self, value: float):
        with self.lock:
            self.reserved.append(value)

    def clear(self):
        with self.lock:
            self.reserved.clear()
            self.stack.clear()

    def latest(self, seconds: int = 1):
        with self.lock:
            list_ = list(self.stack)
        length = (seconds // self.interval) + 1
        start = (length - 1) * self.interval * -1
        padding = self.stack[0] if len(self.stack) > 0 else 0
        deficient = length - len(list_)
        list_ = [padding] * deficient + list_
        x = numpy.arange(start, 1, self.interval)
        y = numpy.asarray(list_[length * -1:], dtype=float)
        return x, y


class StreamPlotter:

    def __init__(self, title: str = None):
        japanize_matplotlib.japanize()
        matplotlib.rcParams["toolbar"] = "None"
        matplotlib.rcParams["lines.marker"] = "."
        matplotlib.pyplot.show()
        figure = matplotlib.pyplot.figure(title)
        figure.canvas.mpl_connect("close_event", self.close)
        self.figure = figure

    def close(self, _):
        sys.exit(0)

    def update(self):
        list_ = self.figure.axes
        lines = itertools.chain.from_iterable([x.lines for x in list_])
        for line in lines:
            Line2D(line).update()

    def run(self, interval: int = 1):
        def decorator(function):
            def wrapper(*args, **kwargs):
                basetime = time.time()
                while True:
                    function(*args, **kwargs)
                    matplotlib.pyplot.pause(0.1)
                    elapsed = time.time() - basetime
                    seconds = elapsed + (interval - elapsed % interval)
                    basetime += seconds
                    while time.time() < basetime:
                        time.sleep(0.1)
            return wrapper
        return decorator


class Figure:

    def __init__(self, entity: matplotlib.figure.Figure):
        self.entity = entity

    def grid(self, count: int = None):
        length = len(self.entity.axes)
        count = length if count is None else count
        sqrt = math.sqrt(count)
        rounded = round(sqrt, 0)
        nrows = math.ceil(sqrt)
        ncols = int(rounded)
        return nrows, ncols

    def rearrange(self, count: int = None):
        length = len(self.entity.axes)
        nrows, ncols = self.grid(count)
        for index in range(length):
            axes = self.entity.add_subplot(nrows, ncols, index+1)
            bbox = axes.get_position()
            self.entity.delaxes(axes)
            self.entity.axes[index].set_position(bbox)

    def extract(self, uuid4: uuid.UUID):
        list_ = [x for x in self.entity.axes if x.id == uuid4]
        axes = Axes(list_[0]) if len(list_) > 0 else None
        return axes

    def append(self, title: str = None):
        length = len(self.entity.axes)
        count = length + 1
        self.rearrange(count)
        nrows, ncols = self.grid(count)
        axes = self.entity.add_subplot(nrows, ncols, count)
        axes.plot()
        axes.grid()
        axes.set_title(title)
        axes.id = uuid.uuid4()
        axes.xrange = (-100, 0)
        axes.yrange = (None, None)
        axes = Axes(axes)
        return axes

    def remove(self, uuid4: uuid.UUID):
        axes = self.extract(uuid4)
        self.entity.delaxes(axes.entity)
        self.rearrange()


class Axes:

    def __init__(self, entity: matplotlib.pyplot.Axes):
        self.entity = entity

    def extract(self, uuid4: uuid.UUID):
        list_ = [x for x in self.entity.lines if x.id == uuid4]
        line = Line2D(list_[0]) if len(list_) > 0 else None
        return line

    def append(self, label: str = None):
        if label is None:
            index = len(self.entity.lines) + 1
            label = f"系列{index}"
        data = DataStream()
        x, y = data.latest(self.seconds)
        self.entity.plot(x, y, label=label)
        self.entity.legend()
        line = self.entity.lines[-1]
        line.id = uuid.uuid4()
        line.data = data
        line = Line2D(line)
        return line

    def remove(self, uuid4: uuid.UUID):
        line = self.extract(uuid4)
        line.entity.remove()
        if len(self.entity.lines) > 0:
            self.entity.legend()
        else:
            self.entity.legend().remove()

    def get_xrange(self):
        left = self.seconds * -1
        right = 0
        diff = right - left
        margin = diff * 0.05 if diff > 0 else 0.05
        left = left - margin
        right = right + margin
        return left, right

    def get_yrange(self):
        lines = [Line2D(x) for x in self.entity.lines]
        data = [x.data.latest(self.seconds)[1] for x in lines]
        data = numpy.concatenate(data) if len(data) > 0 else None
        min_value = numpy.nan if data is None else numpy.nanmin(data)
        min_value = 0.0 if numpy.isnan(min_value) else min_value
        max_value = numpy.nan if data is None else numpy.nanmax(data)
        max_value = 0.0 if numpy.isnan(max_value) else max_value
        diff = max_value - min_value
        margin = diff * 0.1 if diff > 0 else 0.05
        bottom = min_value - margin if self.bottom is None else self.bottom
        top = max_value + margin if self.top is None else self.top
        bottom = top if (bottom > top and self.bottom is None) else bottom
        top = bottom if (bottom > top and self.top is None) else top
        return bottom, top

    def set_xrange(self, seconds: int = 100):
        seconds = seconds if seconds > 0 else self.seconds
        self.entity.xrange = (seconds * -1, 0)

    def set_yrange(self, bottom: float = None, top: float = None):
        self.entity.yrange = (bottom, top)

    @property
    def id(self) -> uuid.UUID:
        uuid4 = self.entity.id
        return uuid4

    @property
    def title(self) -> str:
        str_ = self.entity.get_title()
        return str_

    @property
    def unit(self) -> str:
        str_ = self.entity.get_ylabel()
        return str_

    @property
    def seconds(self) -> int:
        int_ = self.entity.xrange[0] * -1
        return int_

    @property
    def bottom(self) -> float:
        float_ = self.entity.yrange[0]
        return float_

    @property
    def top(self) -> float:
        float_ = self.entity.yrange[1]
        return float_


class Line2D:

    def __init__(self, entity: matplotlib.lines.Line2D):
        self.entity = entity

    def update(self):
        axes = Axes(self.entity.axes)
        x, y = self.entity.data.latest(axes.seconds)
        self.entity.set_xdata(x)
        self.entity.set_ydata(y)
        xrange = axes.get_xrange()
        yrange = axes.get_yrange()
        self.entity.axes.set_xlim(*xrange)
        self.entity.axes.set_ylim(*yrange)

    @property
    def id(self) -> uuid.UUID:
        uuid4 = self.entity.id
        return uuid4

    @property
    def label(self) -> str:
        str_ = self.entity.get_label()
        return str_

    @property
    def interval(self) -> int:
        int_ = self.data.interval
        return int_

    @property
    def data(self) -> DataStream:
        data = self.entity.data
        return data

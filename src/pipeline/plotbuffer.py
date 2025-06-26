# src/pipeline/plotbuffer.py
from collections import defaultdict

class PlotBuffer_dead:
    def __init__(self, max_length=100):
        self.max_length = max_length
        self.data = defaultdict(lambda: {"x": [], "y": []})

    def append(self, label, x, y):
        series = self.data[label]
        series["x"].append(x)
        series["y"].append(y)
        if len(series["x"]) > self.max_length:
            series["x"].pop(0)
            series["y"].pop(0)

    def get_all(self):
        return self.data

class PlotBuffer:
    def __init__(self, max_points=100):
        from collections import defaultdict
        self.data = defaultdict(lambda: {"x": [], "y": []})
        self.max_points = max_points

    def append(self, label, x, y):
        self.data[label]["x"].append(x)
        self.data[label]["y"].append(y)

        if len(self.data[label]["x"]) > self.max_points:
            self.data[label]["x"].pop(0)
            self.data[label]["y"].pop(0)

    def get_all(self):
        return self.data

# src/pipeline/plotbuffer.py
from collections import defaultdict

class PlotBuffer:
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

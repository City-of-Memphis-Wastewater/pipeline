# src/pipeline/plotbuffer.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from collections import defaultdict


KEEP_ALL_LIVE_POINTS = True

class PlotBuffer:
    def __init__(self, max_points=100):
        self.data = defaultdict(lambda: {"x": [], "y": []})
        self.max_points = max_points

    def append(self, label, x, y):
        self.data[label]["x"].append(x)
        self.data[label]["y"].append(y)

        if len(self.data[label]["x"]) > self.max_points:
            if not KEEP_ALL_LIVE_POINTS:
                self.data[label]["x"].pop(0)
                self.data[label]["y"].pop(0)

    def get_all(self):
        return self.data

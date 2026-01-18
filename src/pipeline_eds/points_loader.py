# src/points_loader.py

from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import csv

class PointsCsvLoader:
    """
    loader = PointsCsvLoader(csv_path)
    points_list = loader.load_points()
    """
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.points = []

    def load_points(self):
        with open(self.csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.points.append(row)
        return self.points
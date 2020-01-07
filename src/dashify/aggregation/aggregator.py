from typing import List, Dict
from pandas import DataFrame
import numpy as np


class DataAggregator:
    def __init__(self, experiments_df: DataFrame, smoothing: float=0.0):
        self.experiments_df = experiments_df
        self.smoothing = smoothing

    def group_by_param(self, metric_tag: str, group_by_params: List[str]) -> Dict:
        df = self.experiments_df.copy()
        for param in group_by_params:
            df[param] = df[param].apply(str)
        grouped = df.groupby(group_by_params)
        grouped_dict = {}
        for param_name, param_group in grouped:
            data_series = param_group[metric_tag].values.tolist()
            data = [DataAggregator.smooth(data, self.smoothing) if isinstance(data, list) else [] for data in data_series]
            grouped_dict[f"Group: {group_by_params}"] = data
        return grouped_dict

    @staticmethod
    def smooth(values: List[float], weight: float) -> List[float]:
        if len(values) <= 1:
            return values

        last = values[0]
        smoothed = []
        for point in values:
            smoothed_val = last * weight + (1 - weight) * point
            smoothed.append(smoothed_val)
            last = smoothed_val

        return smoothed
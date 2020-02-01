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
            group_name = self._pretty_name(group_by_params, param_name)
            grouped_dict[group_name] = data
        return grouped_dict

    def _pretty_name(self, group_by_params, param_values):
        param_values = list(param_values) if isinstance(param_values, tuple) else list([param_values])
        group_name = ""
        for param_name, param_value in zip(group_by_params, param_values):
            group_name += f"{param_name}={param_value}_"
        group_name = group_name[0:len(group_name)-1]
        return group_name

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
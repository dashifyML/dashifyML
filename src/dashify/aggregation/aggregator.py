from typing import List, Dict
from pandas import DataFrame
import numpy as np


class DataAggregator:
    def __init__(self, experiments_df: List[DataFrame], smoothing=0.0):
        self.data_df = DataAggregator._get_combined_df(experiments_df)
        self.smoothing = smoothing

    @staticmethod
    def _get_combined_df(experiments_df) -> DataFrame:
        combined_df = DataFrame()
        for exp_df in experiments_df:
            combined_df = combined_df.append(exp_df)
        return combined_df

    def group_by_param(self, metric_tag, group_by_param) -> Dict:
        df = self.data_df.copy()
        df[group_by_param] = df[group_by_param].apply(str)
        grouped = df.groupby([group_by_param])
        grouped_dict = {}
        for param_name, param_group in grouped:
            data_series = param_group[metric_tag].values.tolist()
            data = [DataAggregator.smooth(data, self.smoothing) for data in data_series]
            grouped_dict[f"Group: {group_by_param} with {param_name}"] = np.array(data)
        return grouped_dict

    @staticmethod
    def smooth(values: List[float], weight: float) -> List[float]:
        last = values[0]
        smoothed = []
        for point in values:
            smoothed_val = last * weight + (1 - weight) * point
            smoothed.append(smoothed_val)
            last = smoothed_val

        return smoothed
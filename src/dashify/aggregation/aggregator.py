import pandas as pd
from dashify.data_import.data_reader import Experiment
from typing import List, Dict
from pandas import DataFrame
from dashify.data_import.data_table import DataTable
import numpy as np
from dashify import log_dir_path


class DataAggregator:
    def __init__(self, experiments: List[Experiment]):
        self.data_df = self._get_combined_df(experiments)

    @staticmethod
    def _get_combined_df(experiments: List[Experiment]) -> DataFrame:
        combined_df = DataFrame()
        for exp in experiments:
            df = DataFrame()

            # data
            for metric_tag, metric_data in exp.metrics.items():
                df[metric_tag] = metric_data

            # config params
            for param, value in DataTable.flatten_dict(exp.config).items():
                df[param] = str(value)

            # exp id
            df["identifier"] = exp.identifier
            combined_df = combined_df.append(df)
        return combined_df

    def group_by_param(self, metric_tag, group_by_param) -> Dict:
        grouped = self.data_df.groupby([group_by_param])
        grouped_dict = {}
        for param_name, param_group in grouped:
            data = []
            for exp_name, exp_group in param_group.groupby(["identifier"]):
                data.append(exp_group[metric_tag].values.tolist())
            grouped_dict[f"Group: {group_by_param} with {param_name}"] = np.array(data)

        return grouped_dict


if __name__ == "__main__":
    from dashify.data_import.data_reader import GridSearchLoader
    from dashify.data_import.data_table import DataTable
    loader = GridSearchLoader(grid_search_path=log_dir_path)
    exps = [loader.get_experiment(exp_id) for exp_id in loader.get_experiment_ids()]
    aggregator = DataAggregator(experiments=exps)
    print(aggregator.group_by_param("train/loss_classification", group_by_param="trainer/sampling"))
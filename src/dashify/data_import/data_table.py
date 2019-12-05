from dashify.data_import.data_reader import GridSearchLoader
import collections
import pandas as pd
from typing import List, Dict

class DataTable:
    def __init__(self, gs_loader: GridSearchLoader):
        self.gs_loader = gs_loader

        self.experiment_ids = gs_loader.get_experiment_ids()
        self.flattened_configs = [DataTable.flatten_dict(gs_loader.get_experiment(experiment_id).config) for experiment_id in
                             self.experiment_ids]
        self.flattened_metrics = [DataTable.flatten_dict(gs_loader.get_experiment(experiment_id).metrics) for experiment_id
                             in
                             self.experiment_ids]

    @staticmethod
    def flatten_dict(d, parent_key='', sep='/'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(DataTable.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def get_config_columns(self):
        return list(set(key for config in self.flattened_configs for key in config))

    def get_metrics_columns(self):
        return list(set(key for metrics in self.flattened_metrics for key in metrics))

    def to_pandas_data_frame(self) -> pd.DataFrame:
        df = pd.concat([pd.DataFrame(self.experiment_ids, columns=["experiment_id"]),
                         pd.DataFrame(self.flattened_configs),
                         pd.DataFrame(self.flattened_metrics)], axis=1)
        df = df.set_index("experiment_id")
        return df

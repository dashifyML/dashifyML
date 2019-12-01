from dashify.data_import.data_reader import GridSearchLoader
import collections
import pandas as pd


class DataTable:
    def __init__(self, gs_loader: GridSearchLoader):
        self.gs_loader = gs_loader

        experiment_ids = gs_loader.get_experiment_ids()
        self.flattened_configs = [DataTable.flatten_dict(gs_loader.get_experiment(experiment_id).config) for experiment_id in
                             experiment_ids]
        flattened_metrics = [DataTable.flatten_dict(gs_loader.get_experiment(experiment_id).metrics) for experiment_id
                             in
                             experiment_ids]

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

    def to_pandas_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.flattened_configs)


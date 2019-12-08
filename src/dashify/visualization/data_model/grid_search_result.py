from dashify.visualization.data_model.experiment import Experiment
from typing import List
import collections
import pandas as pd

class GridSearchResult:
    def __init__(self, log_dir: str, experiments: List[Experiment] = None):
        """
        Dataclass for storing all the experiments of a grid search.
        :param log_dir: Experiments' logging directory of the grid search
        :param experiments: List of experiments
        """
        self.log_dir = log_dir
        if experiments is None:
            experiments = []
        self.experiments = experiments

    def add_experiment(self, experiment: Experiment):
        """
        Adds an experiment to the grid search
        :param experiment: Experiment object
        :return: None
        """
        self.experiments.append(experiment)

    def get_experiment_ids(self) -> List[str]:
        """
        Returns all expriment ids of the grid search
        :return: List[experiment_id]
        """
        return [experiment.identifier for experiment in self.experiments]

    def get_flattened_experiment_configs(self) -> List[str]:
        """
        Returns a list of all flattened config keys present in the grid search
        :return: List of flattened config keys
        """
        flattened_config_keys = []
        for experiment in self.experiments:
            keys = list(GridSearchResult._flatten_dict(experiment.config).keys())
            flattened_config_keys = flattened_config_keys + keys
        return list(set(flattened_config_keys))

    def get_experiment_metrics(self) -> List[str]:
        """
        Returns a list of all metric keys present in the grid search
        :return: List of metric keys
        """
        metrics_keys = []
        for experiment in self.experiments:
            keys = list(experiment.metrics.keys())
            metrics_keys = metrics_keys + keys
        return list(set(metrics_keys))

    def to_pandas_dataframe(self) -> pd.DataFrame:
        metrics = []
        configs = []
        for experiment in self.experiments:
            metrics.append(GridSearchResult._flatten_dict(experiment.metrics))
            configs.append(GridSearchResult._flatten_dict(experiment.config))
        col_sorting = list(metrics[0].keys())
        df = pd.concat([pd.DataFrame(configs), pd.DataFrame(metrics)], axis=1)
        return df

    @staticmethod
    def _flatten_dict(d, parent_key='', sep='/'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(GridSearchResult._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)







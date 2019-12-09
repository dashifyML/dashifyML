import json
import glob
import os
from dashify.visualization.data_model.grid_search_result import GridSearchResult
from dashify.visualization.data_model.experiment import Experiment
from typing import Dict, List


class LocalDataLoader:
    """
    Static class that loads the experiments of a given grid search from disk
    and creates a `GridSearchResult` object.
    """

    @staticmethod
    def get_grid_search_results(gs_log_dir: str) -> GridSearchResult:
        """
        Creates a `GridSearchResult` from a given logging directory.
        :param gs_log_dir: Path to grid search logs
        :return: GridSearchResult
        """
        gs_result = GridSearchResult(gs_log_dir)
        config_paths = glob.glob(os.path.join(gs_log_dir, "**/config.json"), recursive=True)
        metric_paths = glob.glob(os.path.join(gs_log_dir, "**/metrics.json"), recursive=True)

        LocalDataLoader._check_integrity_of_logs(config_paths, metric_paths)

        # load configs and metrics into dictionaries (experiment_id -> loaded_resource)
        configs = {LocalDataLoader._resource_path_to_experiment_id(config_path, gs_log_dir): LocalDataLoader._load_file(resource_path=config_path)
                   for config_path in config_paths}
        metrics = {LocalDataLoader._resource_path_to_experiment_id(metric_path, gs_log_dir): LocalDataLoader._load_file(resource_path=metric_path)
                   for metric_path in metric_paths}

        # create experiment and store in grid search result object
        for experiment_id in configs.keys():
            experiment = Experiment(config=configs[experiment_id],
                                    metrics=metrics[experiment_id],
                                    identifier=experiment_id)
            gs_result.add_experiment(experiment)
        return gs_result

    @staticmethod
    def _check_integrity_of_logs(config_paths: List[str], metric_paths: List[str]):
        """
        Makes sure that each experiment has all files present.
        :param config_paths: List of config file paths
        :param metric_paths: List of metric file paths
        :return:
        """
        experiments_configs = [os.path.dirname(c) for c in config_paths]
        experiments_metrics = [os.path.dirname(m) for m in metric_paths]
        intersection = [e for e in experiments_metrics if e in experiments_configs]
        if len(intersection) != len(experiments_configs) or len(intersection) != len(experiments_metrics):
            raise Exception("Dataset corrupt!!!")

    @staticmethod
    def _load_file(resource_path: str):
        with open(resource_path, "r") as f:
            return json.load(f)

    @staticmethod
    def _resource_path_to_experiment_id(experiment_file_path: str, gs_log_dir: str) -> str:
        """
        Maps the file path of a config or metrics file to the respective experiment id.
        :param experiment_file_path:
        :param gs_log_dir:
        :return:
        """
        return os.path.dirname(os.path.relpath(experiment_file_path, gs_log_dir))

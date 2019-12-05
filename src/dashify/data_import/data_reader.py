import json
import glob
import os


class Experiment:
    def __init__(self, config=None, metrics=None, identifier=None):
        self._config = config
        self._metrics = metrics
        self._identifier = identifier

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    @property
    def metrics(self):
        return self._metrics

    @metrics.setter
    def metrics(self, value):
        self._metrics = value

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, value):
        self._identifier = value


class GridSearchLoader:
    def __init__(self, grid_search_path):
        self.grid_search_path = grid_search_path
        config_paths = glob.glob(os.path.join(grid_search_path, "**/config.json"), recursive=True)
        metric_paths = glob.glob(os.path.join(grid_search_path, "**/metrics.json"), recursive=True)

        self.check_integrity_of_logs(config_paths, metric_paths)

        # load configs and metrics into dictionaries (experiment_id -> loaded_resource)
        configs = {self.resource_path_to_experiment_id(config_path): self._load_file(resource_path=config_path) for
                   config_path in config_paths}
        metrics = {self.resource_path_to_experiment_id(metric_path): self._load_file(resource_path=metric_path) for
                   metric_path in metric_paths}

        # store configs and metrics in proper Experiment objects
        self.experiments = {experiment_id: Experiment(config=configs[experiment_id],
                                                      metrics=metrics[experiment_id],
                                                      identifier=experiment_id)
                            for experiment_id in configs.keys()}

    def check_integrity_of_logs(self, configs, metrics):
        experiments_configs = [os.path.dirname(c) for c in configs]
        experiments_metrics = [os.path.dirname(m) for m in metrics]
        intersection = [e for e in experiments_metrics if e in experiments_configs]
        if len(intersection) != len(experiments_configs) or len(intersection) != len(experiments_metrics):
            raise Exception("Dataset corrupt!!!")

    def _load_file(self, resource_path: str):
        with open(resource_path, "r") as f:
            return json.load(f)

    def get_experiment_ids(self):
        return list(self.experiments.keys())

    def get_experiment(self, id: str) -> Experiment:
        return self.experiments[id]

    def resource_path_to_experiment_id(self, resource_path: str) -> str:
        return os.path.dirname(os.path.relpath(resource_path, self.grid_search_path))


if __name__ == '__main__':
    from dashify import log_dir_path
    gs_loader = GridSearchLoader(log_dir_path)
    print(gs_loader.get_experiment_ids())

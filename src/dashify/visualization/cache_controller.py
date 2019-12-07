from dashify.visualization.data_import.data_loaders import LocalDataLoader
import pandas as pd
from typing import List, Dict
from dashify.visualization.data_model.grid_search_result import GridSearchResult


class InMemoryCacheController:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.cache: Dict[str, SessionStorage] = dict()

    def invalidate_cache(self, session_id: str):
        # reload grid search results from disk
        gs_result = LocalDataLoader.get_grid_search_results(self.log_dir)
        config_dict = {key: True for key in gs_result.get_flattened_experiment_configs()}
        config_settings = ConfigSettings(config_dict)
        metrics_settings = MetricsSettings(tracked_metrics=gs_result.get_experiment_metrics(),
                                           config_settings=config_settings)
        self.cache[session_id] = SessionStorage(gridsearch_result=gs_result,
                                                metrics_settings=metrics_settings,
                                                config_settings=config_settings)

    def get_configs_settings(self, session_id: str):
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].config_settings.config_dict

    def get_metrics_settings(self, session_id: str):
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].metrics_settings.metrics_settings_table


class ConfigSettings:
    def __init__(self, config_dict: Dict[str, bool]):
        self._config_dict: Dict[str, bool] = config_dict

    @property
    def config_dict(self) -> Dict[str, bool]:
        return self._config_dict

    @config_dict.setter
    def config_dict(self, value: Dict[str, bool]):
        self._config_dict = value


class MetricsSettings:
    _supported_aggregation_function = ["max", "min", "mean"]
    _supported_std_band_values = ["n", "y"]
    _supported_selected_band_values = ["y", "n"]

    def __init__(self, tracked_metrics: List[str], config_settings: ConfigSettings):
        self._metrics_settings_table = pd.DataFrame.from_dict({"metrics": tracked_metrics})
        self._metrics_settings_table["Selected"] = MetricsSettings._supported_selected_band_values[0]
        self._metrics_settings_table["Aggregation"] = MetricsSettings._supported_aggregation_function[0]
        self._metrics_settings_table["Std_band"] = MetricsSettings._supported_std_band_values[0]
        self._metrics_settings_table["Grouping parameter"] = list(config_settings.config_dict.keys())[0]

    @property
    def metrics_settings_table(self) -> pd.DataFrame:
        return self._metrics_settings_table

    @metrics_settings_table.setter
    def metrics_settings_table(self, value: pd.DataFrame):
        self._metrics_settings_table = value


class SessionStorage:
    def __init__(self, gridsearch_result: GridSearchResult, metrics_settings: MetricsSettings, config_settings: ConfigSettings):
        self._gridsearch_result = gridsearch_result
        self._metrics_settings = metrics_settings
        self._config_settings = config_settings

    @property
    def gridsearch_result(self) -> GridSearchResult:
        return self._gridsearch_result

    @gridsearch_result.setter
    def gridsearch_result(self, value: GridSearchResult):
        self._gridsearch_result = value

    @property
    def metrics_settings(self) -> MetricsSettings:
        return self._metrics_settings

    @metrics_settings.setter
    def metrics_settings(self, value: MetricsSettings):
        self._metrics_settings = value

    @property
    def config_settings(self) -> ConfigSettings:
        return self._config_settings

    @config_settings.setter
    def config_settings(self, value: ConfigSettings):
        self._config_settings = value


cache_controller = InMemoryCacheController(log_dir="/home/mluebberin/repositories/github/dashify/sample_gs")


if __name__ == '__main__':
    cache_controller.invalidate_cache("a")
    print("abc")



from dashify.visualization.data_import.data_loaders import LocalDataLoader
import pandas as pd
from typing import List, Dict, Tuple
from dashify.visualization.data_model.grid_search_result import GridSearchResult


class InMemoryCacheController:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.cache: Dict[str, SessionStorage] = dict()

    def invalidate_cache(self, session_id: str):
        print(f"Invalidating cache for {session_id}.")
        # reload grid search results from disk
        gs_result = LocalDataLoader.get_grid_search_results(self.log_dir)
        config_dict = {key: True for key in gs_result.get_flattened_experiment_configs()}
        config_settings = ConfigSettings(config_dict)
        metrics_settings = MetricsSettings(tracked_metrics=gs_result.get_experiment_metrics(),
                                           config_settings=config_settings)
        gs_table = GridSearchTableFilters()

        self.cache[session_id] = SessionStorage(gridsearch_result=gs_result,
                                                metrics_settings=metrics_settings,
                                                config_settings=config_settings,
                                                gs_table=gs_table)

    def get_gs_results(self, session_id: str) -> GridSearchResult:
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].gridsearch_result

    def get_configs_settings(self, session_id: str) -> List[str]:
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].config_settings.get_all()

    def get_selected_configs_settings(self, session_id: str) -> List[str]:
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].config_settings.get_selected()

    def set_selected_configs_settings(self, session_id: str, selected_configs: List[str]):
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].config_settings.set_selected(selected_configs)

    def get_metrics_settings(self, session_id: str) -> pd.DataFrame:
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].metrics_settings.metrics_settings_table.copy()

    def set_metrics_settings(self, session_id: str, metrics_settings_table: pd.DataFrame):
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        self.cache[session_id].metrics_settings.metrics_settings_table = metrics_settings_table

    def set_gs_table_filters(self, session_id: str, filters: str):
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        self.cache[session_id].gs_table.set_filters(filters)

    def get_gs_table_filters(self, session_id: str) -> str:
        if session_id not in self.cache:
            self.invalidate_cache(session_id)
        return self.cache[session_id].gs_table.get_filters()


#################################################################
##################### STUFF THAT WE CACHE #######################
#################################################################


class ConfigSettings:
    def __init__(self, config_dict: Dict[str, bool]):
        self._config_dict: Dict[str, bool] = config_dict

    def get_selected(self):
        return [key for key, value in self._config_dict.items() if value]

    def get_all(self):
        return [key for key, value in self._config_dict.items()]

    def set_selected(self, selected: List[str]):
        self._config_dict = {key: key in selected for key, value in self._config_dict.items()}


class MetricsSettings:
    _supported_aggregation_function = ["max", "min", "mean"]
    _supported_std_band_values = ["n", "y"]
    _supported_selected_band_values = ["y", "n"]

    def __init__(self, tracked_metrics: List[str], config_settings: ConfigSettings):
        self._metrics_settings_table = pd.DataFrame.from_dict({"metrics": tracked_metrics})
        self._metrics_settings_table["Selected"] = MetricsSettings._supported_selected_band_values[0]
        self._metrics_settings_table["Aggregation"] = MetricsSettings._supported_aggregation_function[0]
        self._metrics_settings_table["Std_band"] = MetricsSettings._supported_std_band_values[0]
        self._metrics_settings_table["Grouping parameter"] = config_settings.get_all()[0]

    @property
    def metrics_settings_table(self) -> pd.DataFrame:
        return self._metrics_settings_table

    @metrics_settings_table.setter
    def metrics_settings_table(self, value: pd.DataFrame):
        self._metrics_settings_table = value


class GridSearchTableFilters:
    _filter_operators = [['ge ', '>='],
                         ['le ', '<='],
                         ['lt ', '<'],
                         ['gt ', '>'],
                         ['ne ', '!='],
                         ['eq ', '='],
                         ['contains '],
                         ['datestartswith ']]

    def __init__(self, filters: List[str] = None):
        if filters is None:
            filters = []
        self.filters = filters

    def set_filters(self, filter_string: str):
        self.filters = filter_string.split(' && ')

    def get_filters(self) -> str:
        return ' && '.join(self.filters)


class SessionStorage:
    def __init__(self, gridsearch_result: GridSearchResult, metrics_settings: MetricsSettings,
                 config_settings: ConfigSettings, gs_table: GridSearchTableFilters):
        self._gridsearch_result = gridsearch_result
        self._metrics_settings = metrics_settings
        self._config_settings = config_settings
        self._gs_table = gs_table

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

    @property
    def gs_table(self) -> GridSearchTableFilters:
        return self._gs_table

    @gs_table.setter
    def gs_table(self, value: GridSearchTableFilters):
        self._gs_table = value


cache_controller = InMemoryCacheController(log_dir="/home/mluebberin/repositories/github/dashify/sample_gs")

if __name__ == '__main__':
    cache_controller.invalidate_cache("a")
    print("abc")

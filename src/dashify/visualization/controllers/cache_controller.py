from dashify.visualization.data_import.data_loaders import LocalDataLoader
import pandas as pd
from typing import List, Dict, Optional
from dashify.visualization.data_model.grid_search_result import GridSearchResult
import os
import functools


class InMemoryCacheController:
    def __init__(self, log_dir: str = None):
        self.cache: Dict[str, Dict[str, SessionStorage]] = dict()
        self._log_dir = log_dir

    @property
    def log_dir(self) -> str:
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value: str):
        self._log_dir = value

    def create_on_access(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        return wrapper

    def invalidate_cache(self, grid_search_id: str, session_id: str):
        print(f"Invalidating cache for {session_id, grid_search_id}.")
        if session_id not in self.cache:
            self.cache[session_id] = dict()

        # reload grid search results from disk
        gs_result = LocalDataLoader.get_grid_search_results(os.path.join(self.log_dir, grid_search_id))
        config_dict = {key: True for key in gs_result.get_flattened_experiment_configs()}
        config_settings = ConfigSettings(config_dict)
        metrics_settings = MetricsSettings(tracked_metrics=gs_result.get_experiment_metrics(),
                                           config_settings=config_settings)
        experiment_filters = ExperimentFilters()
        graph_settings = GraphSettings()
        self.cache[session_id][grid_search_id] = SessionStorage(gridsearch_result=gs_result,
                                                                metrics_settings=metrics_settings,
                                                                config_settings=config_settings,
                                                                experiment_filters=experiment_filters,
                                                                graph_settings=graph_settings)
        # self.activate_grid_search(session_id, grid_search_id)

    def get_activated_grid_search_id(self, session_id) -> Optional[str]:
        if session_id not in self.cache:
            return None
        for grid_search_id, session_storage in self.cache[session_id].items():
            if session_storage.active:
                return grid_search_id
        return None

    def activate_grid_search(self, session_id: str, grid_search_id: str):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        for gs_id, session_storage in self.cache[session_id].items():
            self.cache[session_id][gs_id].active = grid_search_id == gs_id

    def get_gs_results(self, grid_search_id: str, session_id: str, reload=False) -> GridSearchResult:
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        elif reload:
            gs_result = LocalDataLoader.get_grid_search_results(os.path.join(self.log_dir, grid_search_id))
            self.cache[session_id][grid_search_id].gridsearch_result = gs_result
        return self.cache[session_id][grid_search_id].gridsearch_result

    def get_configs_settings(self, grid_search_id: str, session_id: str) -> List[str]:
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        return self.cache[session_id][grid_search_id].config_settings.get_all()

    def get_selected_configs_settings(self, grid_search_id: str, session_id: str) -> List[str]:
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        selected_configs = self.cache[session_id][grid_search_id].config_settings.get_selected()
        return selected_configs

    def set_selected_configs_settings(self, grid_search_id: str, session_id: str, selected_configs: List[str]):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        self.cache[session_id][grid_search_id].config_settings.set_selected(selected_configs)

    def get_metrics_settings(self, grid_search_id: str, session_id: str) -> pd.DataFrame:
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        return self.cache[session_id][grid_search_id].metrics_settings.metrics_settings_table.copy()

    def set_metrics_settings(self, grid_search_id: str, session_id: str, metrics_settings_table: pd.DataFrame):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        self.cache[session_id][grid_search_id].metrics_settings.metrics_settings_table = metrics_settings_table

    def set_experiment_filters(self, grid_search_id: str, session_id: str, filters: List[str]):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        self.cache[session_id][grid_search_id].experiment_filters.filters = filters

    def get_experiment_filters(self, grid_search_id: str, session_id: str) -> List[str]:
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        return self.cache[session_id][grid_search_id].experiment_filters.filters

    def set_graph_smoothing_factor(self, grid_search_id: str, session_id: str, smoothing_factor: float):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        self.cache[session_id][grid_search_id].graph_settings.smoothing_factor = smoothing_factor

    def get_graph_smoothing_factor(self, grid_search_id: str, session_id: str):
        if session_id not in self.cache or grid_search_id not in self.cache[session_id]:
            self.invalidate_cache(grid_search_id, session_id)
        return self.cache[session_id][grid_search_id].graph_settings.smoothing_factor


#################################################################
##################### STUFF THAT WE CACHE #######################
#################################################################

class GraphSettings:
    def __init__(self, smoothing_factor: float = 0):
        self._smoothing_factor = smoothing_factor

    @property
    def smoothing_factor(self) -> float:
        return self._smoothing_factor

    @smoothing_factor.setter
    def smoothing_factor(self, value: float):
        self._smoothing_factor = value


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
    _supported_selected_band_values = ["n", "y"]

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


class ExperimentFilters:
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
        self._filters = filters

    @property
    def filters(self) -> List[str]:
        return self._filters

    @filters.setter
    def filters(self, value: List[str]):
        self._filters = value


class SessionStorage:
    def __init__(self, gridsearch_result: GridSearchResult, metrics_settings: MetricsSettings,
                 config_settings: ConfigSettings, experiment_filters: ExperimentFilters, graph_settings: GraphSettings):
        self._gridsearch_result = gridsearch_result
        self._metrics_settings = metrics_settings
        self._config_settings = config_settings
        self._experiment_filters = experiment_filters
        self._graph_settings = graph_settings
        self._active = False  # determines if this session storage is currently visualized or not

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
    def experiment_filters(self) -> ExperimentFilters:
        return self._experiment_filters

    @experiment_filters.setter
    def experiment_filters(self, value: ExperimentFilters):
        self._experiment_filters = value

    @property
    def graph_settings(self) -> GraphSettings:
        return self._graph_settings

    @graph_settings.setter
    def graph_settings(self, value: GraphSettings):
        self._graph_settings = value

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value


cache_controller = InMemoryCacheController()

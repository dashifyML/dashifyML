from dashify.visualization.controllers.cache_controller import cache_controller
from dashify.visualization.controllers.cache_controller import ExperimentFilters
import dashify.visualization.controllers.cell_data_types  as cell_data_types

import pandas as pd
from typing import List, Tuple
import numpy as np
import os


class GridSearchController:
    @staticmethod
    def get_log_dir() -> str:
        return cache_controller.log_dir

    @staticmethod
    def set_log_dir(log_dir: str, replace=False):
        if cache_controller.log_dir is None or replace:
            cache_controller.log_dir = log_dir
            # TODO invalidate entire cache

    @staticmethod
    def get_gridsearch_ids():
        log_dir = cache_controller.log_dir
        return [name for name in os.listdir(log_dir) if os.path.isdir(os.path.join(log_dir, name))]

    @staticmethod
    def get_activated_grid_search_id(session_id: str) -> str:
        activated_grid_search_id = cache_controller.get_activated_grid_search_id(session_id)
        if activated_grid_search_id is None:
            activated_grid_search_id = GridSearchController.get_gridsearch_ids()[0]
            GridSearchController.set_activated_grid_search_id(session_id, activated_grid_search_id)
        return activated_grid_search_id

    @staticmethod
    def set_activated_grid_search_id(session_id: str, grid_search_id):
        cache_controller.activate_grid_search(session_id, grid_search_id)


class GraphController:
    @staticmethod
    def get_smoothing_factor(session_id: str) -> float:
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        smoothing_factor = cache_controller.get_graph_smoothing_factor(grid_search_id, session_id)
        smoothing_factor = 0.0 if smoothing_factor is None else smoothing_factor
        return smoothing_factor

    @staticmethod
    def set_smoothing_factor(session_id: str, smoothing_factor: float):
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        cache_controller.set_graph_smoothing_factor(grid_search_id, session_id, smoothing_factor)


class MetricsController:
    @staticmethod
    def get_metrics_settings(session_id: str) -> pd.DataFrame:
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        return cache_controller.get_metrics_settings(grid_search_id, session_id)

    @staticmethod
    def set_metrics_settings(session_id: str, metrics_settings_table: pd.DataFrame):
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        cache_controller.set_metrics_settings(grid_search_id, session_id, metrics_settings_table)

    @staticmethod
    def get_selected_metrics(session_id: str):
        return MetricsController.filter_metrics_settings(session_id, "Selected", "y")["metrics"]

    @staticmethod
    def filter_metrics_settings(session_id: str, filter_col: str, filter_value: object):
        df_metrics = MetricsController.get_metrics_settings(session_id)
        return df_metrics[df_metrics[filter_col] == filter_value]

    @staticmethod
    def is_band_enabled_for_metric(session_id, metric_tag):
        settings_df = MetricsController.filter_metrics_settings(session_id, "Std_band", "y")
        settings_df = settings_df[settings_df["metrics"] == metric_tag]
        return settings_df.shape[0] > 0

    @staticmethod
    def get_metric_setting_by_metric_tag(session_id: str, metric_tag: str, setting_col) -> str:
        df_metrics = MetricsController.get_metrics_settings(session_id)
        setting = df_metrics[df_metrics["metrics"] == metric_tag][setting_col].values[0]
        return setting


class ConfigController:
    @staticmethod
    def get_configs_settings(session_id: str) -> List[str]:
        gridsearch_id = GridSearchController.get_activated_grid_search_id(session_id)
        return cache_controller.get_configs_settings(gridsearch_id, session_id)

    @staticmethod
    def get_selected_configs_settings(session_id: str) -> List[str]:
        gridsearch_id = GridSearchController.get_activated_grid_search_id(session_id)
        selected_configs = cache_controller.get_selected_configs_settings(gridsearch_id, session_id)
        return selected_configs

    @staticmethod
    def set_selected_configs_settings(session_id: str, selected_configs: List[str]):
        gridsearch_id = GridSearchController.get_activated_grid_search_id(session_id)
        cache_controller.set_selected_configs_settings(gridsearch_id, session_id, selected_configs)


class ExperimentController:
    @staticmethod
    def get_experiments_df(session_id: str, aggregate: bool = True, reload=False) -> pd.DataFrame:
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        metrics_settings = cache_controller.get_metrics_settings(grid_search_id, session_id)
        config_cols = cache_controller.get_selected_configs_settings(grid_search_id, session_id)
        experiment_filters = cache_controller.get_experiment_filters(grid_search_id, session_id)
        df_experiments = cache_controller.get_gs_results(grid_search_id, session_id,
                                                         reload=reload).to_pandas_dataframe()
        return ExperimentController._process_experiments_df(df_experiments=df_experiments,
                                                            config_cols=config_cols + ["experiment_id"],
                                                            metrics_settings=metrics_settings,
                                                            experiment_filters=experiment_filters,
                                                            aggregate=aggregate)

    @staticmethod
    def refresh(session_id):
        """
        Refreshes the grid search results once (as it writes to InMemory cache already)
        Any views which need live data can call refresh() once when required and access data (subsequently) using controllers with reload = False

        """
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        _ = cache_controller.get_gs_results(grid_search_id, session_id, reload=True).to_pandas_dataframe()

    @staticmethod
    def set_experiment_filters(session_id: str, filters: str):
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        cache_controller.set_experiment_filters(grid_search_id, session_id, filters)

    @staticmethod
    def get_experiment_filters(session_id: str) -> str:
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        return cache_controller.get_experiment_filters(grid_search_id, session_id)

    @staticmethod
    def get_experiment_filters_string(session_id: str) -> str:
        grid_search_id = GridSearchController.get_activated_grid_search_id(session_id)
        return cache_controller.get_experiment_filters(grid_search_id, session_id)

    @staticmethod
    def get_experiment_ids(session_id: str) -> List[str]:
        return ExperimentController.get_experiments_df(session_id)["experiment_id"].tolist()

    @staticmethod
    def get_experiment_data_by_experiment_id(session_id: str, exp_ids: List[str], metric_tags: List[str] = None, reload: bool = False) -> pd.DataFrame:
        df = ExperimentController.get_experiments_df(session_id, False, reload=reload)
        df = df[df["experiment_id"].isin(exp_ids)]
        data = df if metric_tags is None else df[metric_tags + ["experiment_id"]]
        return data

    @staticmethod
    def _process_experiments_df(df_experiments: pd.DataFrame,
                                config_cols: List[str],
                                metrics_settings: pd.DataFrame,
                                experiment_filters: List[str],
                                aggregate: bool) -> pd.DataFrame:
        # filter those columns in the dataframe
        df_selected_metrics = metrics_settings[metrics_settings["Selected"] == "y"]
        metrics_cols = df_selected_metrics["metrics"].tolist()
        # set the columns of the gridsearch table
        df_experiments = ExperimentController._filter_columns(df_experiments, config_cols, metrics_cols)
        # apply aggregation function to the respective columns in the grid search table
        if aggregate:
            df_experiments = ExperimentController._apply_aggregation_functions(df_experiments, df_selected_metrics)
        # filter the respective experiment rows
        df_experiments = ExperimentController._apply_experiment_filters(df_experiments, df_selected_metrics, experiment_filters)
        return df_experiments

    @staticmethod
    def _filter_columns(df: pd.DataFrame, config_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
        columns = config_cols + metric_cols
        columns = [column for column in columns if
                   column in df.columns]  # keep only those columns that are already in the data frame
        return df[columns]

    @staticmethod
    def _apply_aggregation_functions(df_experiments: pd.DataFrame, df_selected_metrics: pd.DataFrame):
        df_experiments = df_experiments.copy()
        agg_fun_dict = {"mean": np.mean, "max": np.max, "min": np.min}
        for index, row in df_selected_metrics.iterrows():
            agg_fun_key = row["Aggregation"]
            agg_fun = agg_fun_dict[agg_fun_key]
            df_experiments[row["metrics"]] = df_experiments[row["metrics"]].apply(agg_fun)
        return df_experiments

    @staticmethod
    def _apply_experiment_filters(df_experiments: pd.DataFrame, df_selected_metrics: pd.DataFrame, filters: List[str]) -> pd.DataFrame:

        col_data_types_dict = cell_data_types.infer_datatypes_for_columns(df_experiments)

        if filters:
            # we want to apply the filters on the aggregate metrics data
            df_experiments_agg = ExperimentController._apply_aggregation_functions(df_experiments, df_selected_metrics)
            # filter the dataframe
            for filter_expression in filters:
                col_name, operator, filter_value = ExperimentController._split_filter_expression(filter_expression)
                if col_name is None:
                    continue
                filter_value = cell_data_types.convert_string_to_supported_data_type(filter_value, col_data_types_dict[col_name])
                if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                    # the dataframe operators also allow for list-like objects which is why we need to wrap the filter_value in another list
                    if col_data_types_dict[col_name] == cell_data_types.SupportedDataTypes.list_type:
                        filter_value = [filter_value]
                    df_experiments_agg = df_experiments_agg.loc[getattr(df_experiments_agg[col_name], operator)(filter_value)]
                elif operator == 'contains':
                    df_experiments_agg = df_experiments_agg.loc[df_experiments_agg[col_name].str.contains(filter_value)]
                elif operator == 'datestartswith':
                    # this is a simplification of the front-end filtering logic,
                    # only works with complete fields in standard format
                    df_experiments_agg = df_experiments_agg.loc[df_experiments_agg[col_name].str.startswith(filter_value)]
            df_experiments = df_experiments[df_experiments["experiment_id"].isin(df_experiments_agg["experiment_id"])]
        return df_experiments

    @staticmethod
    def _split_filter_expression(filter_expression: str) -> Tuple:
        for operator_type in ExperimentFilters._filter_operators:
            for operator in operator_type:
                if operator in filter_expression:
                    name_part, value_part = filter_expression.split(operator, 1)
                    name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                    value_part = value_part.strip()
                    v0 = value_part[0]
                    if v0 == value_part[-1] and v0 in ("'", '"', '`'):
                        value = value_part[1: -1].replace('\\' + v0, v0)
                    else:
                        try:
                            value = float(value_part)
                        except ValueError:
                            value = value_part
                    # word operators need spaces after them in the filter string,
                    # but we don't want these later
                    return name, operator_type[0].strip(), value
        return None, None, None

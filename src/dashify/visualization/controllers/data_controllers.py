from dashify.visualization.controllers.cache_controller import cache_controller
import pandas as pd
from typing import List, Tuple
import numpy as np
from dashify.visualization.controllers.cache_controller import ExperimentFilters


class GraphController:
    @staticmethod
    def get_smoothing_factor(gs_log_dir: str, session_id: str) -> float:
        smoothing_factor = cache_controller.get_graph_smoothing_factor(gs_log_dir, session_id)
        smoothing_factor = 0.0 if smoothing_factor is None else smoothing_factor
        return smoothing_factor

    @staticmethod
    def set_smoothing_factor(gs_log_dir: str, session_id: str, smoothing_factor: float):
        cache_controller.set_graph_smoothing_factor(gs_log_dir, session_id, smoothing_factor)


class MetricsController:
    @staticmethod
    def get_metrics_settings(gs_log_dir: str, session_id: str) -> pd.DataFrame:
        return cache_controller.get_metrics_settings(gs_log_dir, session_id)

    @staticmethod
    def set_metrics_settings(gs_log_dir: str, session_id: str, metrics_settings_table: pd.DataFrame):
        cache_controller.set_metrics_settings(gs_log_dir, session_id, metrics_settings_table)

    @staticmethod
    def get_selected_metrics(gs_log_dir: str, session_id: str):
        return MetricsController.filter_metrics_settings(gs_log_dir, session_id, "Selected", "y")["metrics"]

    @staticmethod
    def filter_metrics_settings(gs_log_dir: str, session_id: str, filter_col: str, filter_value: object):
        df_metrics = MetricsController.get_metrics_settings(gs_log_dir, session_id)
        return df_metrics[df_metrics[filter_col] == filter_value]

    @staticmethod
    def is_band_enabled_for_metric(gs_log_dir, session_id, metric_tag):
        settings_df = MetricsController.filter_metrics_settings(gs_log_dir, session_id, "Std_band", "y")
        settings_df = settings_df[settings_df["metrics"] == metric_tag]
        return settings_df.shape[0] > 0

    @staticmethod
    def get_metric_setting_by_metric_tag(gs_log_dir: str, session_id: str, metric_tag: str, setting_col) -> str:
        df_metrics = MetricsController.get_metrics_settings(gs_log_dir, session_id)
        setting = df_metrics[df_metrics["metrics"] == metric_tag][setting_col].values[0]
        return setting


class ConfigController:
    @staticmethod
    def get_configs_settings(gs_log_dir: str, session_id: str) -> List[str]:
        return cache_controller.get_configs_settings(gs_log_dir, session_id)

    @staticmethod
    def get_selected_configs_settings(gs_log_dir: str, session_id: str) -> List[str]:
        return cache_controller.get_selected_configs_settings(gs_log_dir, session_id)

    @staticmethod
    def set_selected_configs_settings(gs_log_dir: str, session_id: str, selected_configs: List[str]):
        cache_controller.set_selected_configs_settings(gs_log_dir, session_id, selected_configs)


class ExperimentController:
    @staticmethod
    def get_experiments_df(gs_log_dir: str, session_id: str, aggregate: bool = True) -> pd.DataFrame:
        metrics_settings = cache_controller.get_metrics_settings(gs_log_dir, session_id)
        config_cols = cache_controller.get_selected_configs_settings(gs_log_dir, session_id)
        experiment_filters = cache_controller.get_experiment_filters(gs_log_dir, session_id)
        df_experiments = cache_controller.get_gs_results(gs_log_dir, session_id).to_pandas_dataframe()
        return ExperimentController._process_experiments_df(df_experiments=df_experiments,
                                                            config_cols=config_cols+["experiment_id"],
                                                            metrics_settings=metrics_settings,
                                                            experiment_filters=experiment_filters,
                                                            aggregate=aggregate)

    @staticmethod
    def set_experiment_filters(gs_log_dir: str, session_id: str, filters: str):
        cache_controller.set_experiment_filters(gs_log_dir, session_id, filters)

    @staticmethod
    def get_experiment_filters(gs_log_dir: str, session_id: str) -> str:
        return cache_controller.get_experiment_filters(gs_log_dir, session_id)

    @staticmethod
    def get_experiment_filters_string(gs_log_dir: str, session_id: str) -> str:
        return cache_controller.get_experiment_filters(gs_log_dir, session_id)

    @staticmethod
    def get_experiment_ids(gs_log_dir: str, session_id: str) -> List[str]:
        return ExperimentController.get_experiments_df(gs_log_dir, session_id)["experiment_id"].tolist()

    @staticmethod
    def get_experiment_data_by_experiment_id(gs_log_dir, session_id, exp_id, metric_tag=None) -> pd.DataFrame:
        df = ExperimentController.get_experiments_df(gs_log_dir, session_id, False)
        df = df[df["experiment_id"] == exp_id]
        return df if metric_tag is None else df[metric_tag].values[0]

    @staticmethod
    def _process_experiments_df(df_experiments: pd.DataFrame,
                                config_cols: List[str],
                                metrics_settings: pd.DataFrame,
                                experiment_filters: List[str],
                                aggregate: bool) -> pd.DataFrame:
        # filter those columns in the dataframe
        df_selected_metrics = metrics_settings[metrics_settings["Selected"] == "y"]
        metrics_cols = metrics_settings["metrics"].tolist()
        # set the columns of the gridsearch table
        df_experiments = ExperimentController._filter_columns(df_experiments, config_cols, metrics_cols)
        # apply aggregation function to the respective columns in the grid search table
        if aggregate:
            df_experiments = ExperimentController._apply_aggregation_functions(df_experiments, df_selected_metrics)
        # filter the respective experiment rows
        df_experiments = ExperimentController._apply_experiment_filters(df_experiments, experiment_filters)
        return df_experiments

    @staticmethod
    def _filter_columns(df: pd.DataFrame, config_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
        columns = config_cols + metric_cols
        columns = [column for column in columns if
                   column in df.columns]  # keep only those columns that are already in the data frame
        return df[columns]

    @staticmethod
    def _apply_aggregation_functions(df_gs_table: pd.DataFrame, df_aggregation_fun: pd.DataFrame):
        agg_fun_dict = {"mean": np.mean, "max": np.max, "min": np.min}
        for index, row in df_aggregation_fun.iterrows():
            agg_fun_key = row["Aggregation"]
            agg_fun = agg_fun_dict[agg_fun_key]
            df_gs_table[row["metrics"]] = df_gs_table[row["metrics"]].apply(agg_fun)
        return df_gs_table

    @staticmethod
    def _apply_experiment_filters(df_experiments: pd.DataFrame, filters: List[str]) -> pd.DataFrame:
        # filter the dataframe
        for filter_expression in filters:
            col_name, operator, filter_value = ExperimentController._split_filter_expression(filter_expression)
            if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                # these operators match pandas series operator method names
                df_experiments = df_experiments.loc[getattr(df_experiments[col_name], operator)(filter_value)]
            elif operator == 'contains':
                df_experiments = df_experiments.loc[df_experiments[col_name].str.contains(filter_value)]
            elif operator == 'datestartswith':
                # this is a simplification of the front-end filtering logic,
                # only works with complete fields in standard format
                df_experiments = df_experiments.loc[df_experiments[col_name].str.startswith(filter_value)]
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

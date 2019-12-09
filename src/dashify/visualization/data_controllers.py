from dashify.visualization.cache_controller import cache_controller
import pandas as pd
from typing import List, Tuple
import numpy as np
from dashify.visualization.cache_controller import ExperimentFilters


class MetricsController:
    @staticmethod
    def get_metrics_settings(log_dir: str, session_id: str) -> pd.DataFrame:
        return cache_controller.get_metrics_settings(log_dir, session_id)

    @staticmethod
    def set_metrics_settings(log_dir: str, session_id: str, metrics_settings_table: pd.DataFrame):
        return cache_controller.set_metrics_settings(log_dir, session_id, metrics_settings_table)


class ConfigController:
    @staticmethod
    def get_configs_settings(log_dir: str, session_id: str) -> List[str]:
        return cache_controller.get_configs_settings(log_dir, session_id)

    @staticmethod
    def get_selected_configs_settings(log_dir: str, session_id: str) -> List[str]:
        return cache_controller.get_selected_configs_settings(log_dir, session_id)

    @staticmethod
    def set_selected_configs_settings(log_dir: str, session_id: str, selected_configs: List[str]):
        return cache_controller.set_selected_configs_settings(log_dir, session_id, selected_configs)


class ExperimentController:
    @staticmethod
    def get_experiments_df(log_dir: str, session_id: str) -> pd.DataFrame:
        metrics_settings = cache_controller.get_metrics_settings(log_dir, session_id)
        config_cols = cache_controller.get_selected_configs_settings(log_dir, session_id)
        experiment_filters = cache_controller.get_experiment_filters(log_dir, session_id)
        df_experiments = cache_controller.get_gs_results(log_dir, session_id).to_pandas_dataframe()
        return ExperimentController._process_experiments_df(df_experiments=df_experiments,
                                                            config_cols=config_cols,
                                                            metrics_settings=metrics_settings,
                                                            experiment_filters=experiment_filters)

    @staticmethod
    def set_experiment_filters(log_dir: str, session_id: str, filters: str):
        return cache_controller.set_experiment_filters(log_dir, session_id, filters)

    @staticmethod
    def get_experiment_filters(log_dir: str, session_id: str) -> str:
        return cache_controller.get_experiment_filters(log_dir, session_id)

    @staticmethod
    def get_experiment_filters_string(log_dir: str, session_id: str) -> str:
        return cache_controller.get_experiment_filters(log_dir, session_id)

    @staticmethod
    def _process_experiments_df(df_experiments: pd.DataFrame, config_cols: List[str], metrics_settings: pd.DataFrame,
                                experiment_filters: List[str]) -> pd.DataFrame:
        # filter those columns in the dataframe
        df_selected_metrics = metrics_settings[metrics_settings["Selected"] == "y"]
        metrics_cols = metrics_settings["metrics"].tolist()
        # set the columns of the gridsearch table
        df_experiments = ExperimentController._filter_columns(df_experiments, config_cols, metrics_cols)
        # apply aggregation function to the respective columns in the grid search table
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

# THIS STUFF HAS TO GO INTO CACHE CONTROLLER AS WELL
# The gs table tab needs to access and set filters.
# gs table tab and graph tab need to get the filtered gs result. The latter one needs to be able to reload te gs from disc and apply the filters again

from dashify.visualization.cache_controller import cache_controller
import pandas as pd
from typing import List, Tuple
import numpy as np
from dashify.visualization.cache_controller import GridSearchTableFilters


def get_gs_table(session_id: str) -> pd.DataFrame:
    metrics_settings = cache_controller.get_metrics_settings(session_id)
    config_cols = cache_controller.get_selected_configs_settings(session_id)
    df_gs_table = cache_controller.get_gs_results(session_id).to_pandas_dataframe()
    return _process_gridsearch_table_dataframe(df_gs_table=df_gs_table,
                                               config_cols=config_cols,
                                               metrics_settings=metrics_settings)

def get_gs_table_filters(session_id: str) -> str:
    return cache_controller.get_gs_table_filters(session_id)


def _process_gridsearch_table_dataframe(df_gs_table: pd.DataFrame, config_cols: List[str], metrics_settings: pd.DataFrame) -> pd.DataFrame:
    # filter those columns in the dataframe
    df_selected_metrics = metrics_settings[metrics_settings["Selected"] == "y"]
    metrics_cols = metrics_settings["metrics"].tolist()
    # set the columns of the gridsearch table
    df_gs_table = _filter_columns(df_gs_table, config_cols, metrics_cols)
    # apply aggregation function to the respective columns in the grid search table
    df_gs_table = _apply_aggregation_functions(df_gs_table, df_selected_metrics)
    return df_gs_table


def _filter_columns(df: pd.DataFrame, config_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
    columns = config_cols + metric_cols
    columns = [column for column in columns if
               column in df.columns]  # keep only those columns that are already in the data frame
    return df[columns]


def _apply_aggregation_functions(df_gs_table: pd.DataFrame, df_aggregation_fun: pd.DataFrame):
    agg_fun_dict = {"mean": np.mean, "max": np.max, "min": np.min}
    for index, row in df_aggregation_fun.iterrows():
        agg_fun_key = row["Aggregation"]
        agg_fun = agg_fun_dict[agg_fun_key]
        df_gs_table[row["metrics"]] = df_gs_table[row["metrics"]].apply(agg_fun)
    return df_gs_table


def _get_filtered_gs_table(self) -> pd.DataFrame:
    df_gs_table_copy = self.df_gs_table.copy()
    # filter the dataframe
    for filter_expression in self.filters:
        col_name, operator, filter_value = _split_filter_expression(filter_expression)
        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            df_gs_table_copy = df_gs_table_copy.loc[getattr(df_gs_table_copy[col_name], operator)(filter_value)]
        elif operator == 'contains':
            df_gs_table_copy = df_gs_table_copy.loc[df_gs_table_copy[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            df_gs_table_copy = df_gs_table_copy.loc[df_gs_table_copy[col_name].str.startswith(filter_value)]
    return df_gs_table_copy


def _split_filter_expression(filter_expression: str) -> Tuple:
    for operator_type in GridSearchTableFilters._filter_operators:
        for operator in operator_type:
            if operator in filter_expression:
                name_part, value_part = filter_expression.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
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

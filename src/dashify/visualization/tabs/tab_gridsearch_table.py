from dash.dependencies import Input, Output
import dash_table
from dashify.data_import.data_table import DataTable
from dashify.data_import.data_reader import GridSearchLoader
from dashify.visualization.app import app
import pandas as pd
from typing import List
from dashify.visualization.storage.in_memory import server_storage
import numpy as np


def render_table(session_id: str, log_dir: str):
    df_gs_table = load_gridsearch_table(session_id, log_dir)
    filters = get_filters(session_id)
    return dash_table.DataTable(
        id='table-filtering-be',
        columns=[
            {"name": i, "id": i} for i in sorted(df_gs_table.columns)
        ],
        filter_action='custom',
        filter_query=filters
    )


def load_gridsearch_table(session_id: str, log_dir: str) -> pd.DataFrame:
    df_gs_table = server_storage.get(session_id, "grid_search_table")
    if df_gs_table is None:
        df_gs_table = load_gridsearch_table_from_disc(session_id, log_dir)
    return df_gs_table

def load_gridsearch_table_from_disc(session_id: str, log_dir: str) -> pd.DataFrame:
    # load data from disk
    gs_loader = GridSearchLoader(log_dir)
    df_gs_table = DataTable(gs_loader).to_pandas_data_frame()
    # determine the columns to be displayed in the table
    config_cols = server_storage.get(session_id, "Configs")
    metrics_df = server_storage.get(session_id, "Metrics")
    df_gs_table = process_gridsearch_table_dataframe(df_gs_table, config_cols, metrics_df)
    # make the experiment id index a column as well
    df_gs_table = df_gs_table.reset_index()
    return df_gs_table


def get_filters(session_id: str):
    filters = server_storage.get(session_id, "grid_search_table_filters")
    if filters is None:
        return ''
    return filters


def process_gridsearch_table_dataframe(df_gs_table, config_cols, metrics_df):
    # filter those columns in the dataframe
    df_selected_metrics = metrics_df[metrics_df["Selected"] == "y"]
    metrics_cols = metrics_df["metrics"].tolist()
    # set the columns of the gridsearch table
    df_gs_table = filter_columns(df_gs_table, config_cols, metrics_cols)
    # apply aggregation function to the respective columns in the grid search table
    df_gs_table = apply_aggregation_functions(df_gs_table, df_selected_metrics)
    return df_gs_table


def filter_columns(df: pd.DataFrame, config_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
    columns = config_cols + metric_cols
    columns = [column for column in columns if column in df.columns] # keep only those columns that are already in the data frame
    return df[columns]


def apply_aggregation_functions(df_gs_table: pd.DataFrame, df_aggregation_fun: pd.DataFrame):
    agg_fun_dict = {"mean": np.mean, "max": np.max, "min": np.min}
    for index, row in df_aggregation_fun.iterrows():
        agg_fun_key = row["Aggregation"]
        agg_fun = agg_fun_dict[agg_fun_key]
        df_gs_table[row["metrics"]] = df_gs_table[row["metrics"]].apply(agg_fun)
    return df_gs_table


operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
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
    return [None] * 3


@app.callback(
    Output('table-filtering-be', "data"),
    [Input('table-filtering-be', "filter_query"), Input("hidden-log-dir", "children"), Input("session-id", "children")])
def update_table(filter, log_dir, session_id):
    filtering_expressions = filter.split(' && ')
    df_gs_table = load_gridsearch_table_from_disc(session_id, log_dir)

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            df_gs_table = df_gs_table.loc[getattr(df_gs_table[col_name], operator)(filter_value)]
        elif operator == 'contains':
            df_gs_table = df_gs_table.loc[df_gs_table[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            df_gs_table = df_gs_table.loc[df_gs_table[col_name].str.startswith(filter_value)]

    # store filtered grid search table and filters
    server_storage.insert(session_id, "grid_search_table", df_gs_table)
    server_storage.insert(session_id, "grid_search_table_filters", filter)

    return df_gs_table.to_dict('records')

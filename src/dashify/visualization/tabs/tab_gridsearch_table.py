from dash.dependencies import Input, Output
import dash_table
from dashify.data_import.data_table import DataTable
from dashify.data_import.data_reader import GridSearchLoader
from dashify.visualization import Settings
from dashify.visualization.app import app
import pandas as pd
from typing import List, Dict
from dashify.visualization.storage.in_memory import server_storage


def render_table(session_id: str):
    gs_loader = GridSearchLoader(Settings.log_dir)
    df = DataTable(gs_loader).to_pandas_data_frame()
    config_cols = server_storage.get(session_id, "Configs")
    metric_cols = server_storage.get(session_id, "Metrics")
    df = filter_columns(df, config_cols, metric_cols)

    return dash_table.DataTable(
        id='table-filtering-be',
        columns=[
            {"name": i, "id": i} for i in sorted(df.columns)
        ],
        filter_action='custom',
        filter_query=''
    )

def filter_columns(df: pd.DataFrame, config_cols: List[str], metric_cols: List[str]) -> pd.DataFrame:
    columns = config_cols + metric_cols
    columns = [column for column in columns if column in df.columns] # keep only those columns that are already in the data frame
    return df[columns]



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
    [Input('table-filtering-be', "filter_query")])
def update_table(filter):
    filtering_expressions = filter.split(' && ')
    gs_loader = GridSearchLoader(Settings.log_dir)
    df = DataTable(gs_loader).to_pandas_data_frame()
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            df = df.loc[getattr(df[col_name], operator)(filter_value)]
        elif operator == 'contains':
            df = df.loc[df[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            df = df.loc[df[col_name].str.startswith(filter_value)]

    return df.to_dict('records')
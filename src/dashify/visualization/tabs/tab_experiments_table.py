from dash.dependencies import Input, Output
import dash_table
from dashify.visualization.app import app
from dashify.visualization.controllers.data_controllers import ExperimentController
import dash
from flask import url_for
import pandas as pd

def render_table(session_id: str):
    df_experiments = ExperimentController.get_experiments_df(session_id, aggregate=True)
    df_experiments = apply_correct_visualization_values(df_experiments)

    filters = ExperimentController.get_experiment_filters_string(session_id)
    return dash_table.DataTable(
        id='table-filtering-be',
        columns=[
            {"name": i, "id": i} for i in get_sorted_columns(list(df_experiments.columns))
        ],
        filter_action='custom',
        filter_query=' && '.join(filters)
    )

def get_sorted_columns(columns: list):
    columns.remove("experiment_id")
    columns = sorted(columns)
    columns = ["experiment_id"] + columns
    return columns

def apply_correct_visualization_values(df_experiments: pd.DataFrame):
    # correctly render lists
    list_columns = (df_experiments.applymap(type) == list).all()
    list_columns = list_columns.index[list_columns].tolist()
    for col in list_columns:
        df_experiments[col] = df_experiments[col].apply(lambda l: str(l).replace("'", '"'))
    return df_experiments

@app.callback(
    Output('table-filtering-be', "data"),
    [Input('table-filtering-be', "filter_query"), Input("session-id", "children")])
def update_table(filters, session_id):
    ExperimentController.set_experiment_filters(session_id, filters.split(" && "))
    df_experiments = ExperimentController.get_experiments_df(session_id)
    df_experiments = apply_correct_visualization_values(df_experiments)
    return df_experiments.to_dict('records')


@app.callback(
    dash.dependencies.Output('download-exp-link', 'href'),
    [Input('table-filtering-be', "filter_query"), Input("session-id", "children")])
def update_download_link(filters, session_id):
    url = url_for("download_experiments_data", filters=filters)
    return url

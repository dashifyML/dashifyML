from dashify.data_import.data_table import DataTable
from dashify.data_import.data_reader import GridSearchLoader
import dash_html_components as html
from typing import List
from dash.dependencies import Input, Output
import dash_core_components as dcc
from dashify.visualization.app import app
from dashify.visualization.storage.in_memory import server_storage
import dash_table
import pandas as pd
from collections import OrderedDict


def render_settings(session_id: str, log_dir):
    gs_loader = GridSearchLoader(log_dir)
    data_table = DataTable(gs_loader)
    config_settings = create_settings(session_id, data_table.get_config_columns(), "Configs")
    metrics_keys = data_table.get_metrics_columns()
    metrics_settings_table = create_metrics_settings_table(metrics_keys)
    content = html.Div(
        children=[html.H3("What to track?"), html.Div([config_settings, metrics_settings_table], className="row")])
    return content


def create_settings(session_id: str, keys: List[str], settings_type: str):
    keys.sort()
    options = [{'label': key, 'value': key} for key in keys]
    selected_elements = server_storage.get(session_id, settings_type)
    settings = html.Div(
        children=[html.H5(settings_type),
                  dcc.Checklist(
                      options=options,
                      value=selected_elements if selected_elements is not None else keys,
                      id=settings_type
                  )],
        className="three columns"
    )
    return settings


def create_metrics_settings_table(metrics_keys: List[str]):
    agg_fun_list = ["min", "mean", "max"]
    df = pd.DataFrame.from_dict({"metrics": metrics_keys})
    df["Selected"] = "y"
    df["Aggregation"] = agg_fun_list[0]

    table = html.Div([
            html.H5("Metrics"),
            dash_table.DataTable(
                id='table-dropdown',
                data=df.to_dict('records'),
                columns=[
                    {'id': 'metrics', 'name': 'metrics'},
                    {'id': 'Selected', 'name': 'Selected', 'presentation': 'dropdown'},
                    {'id': 'Aggregation', 'name': 'Aggregation', 'presentation': 'dropdown'},
                ],

                editable=True,
                dropdown={
                    'Selected': {
                        'options': [
                            {'label': i, 'value': i}
                            for i in ["y", "n"]
                        ]
                    },
                    'Aggregation': {
                        'options': [
                            {'label': i, 'value': i}
                            for i in agg_fun_list
                        ]
                    }
                }
            ),
            html.Div(id='table-dropdown-container')
        ], className="four columns"
    )
    return table


@app.callback(
    Output('hidden-div-placeholder', "children"),
    [Input('Configs', "value"), Input('Metrics', "value"), Input("session-id", "children")])
def settings_callback(selected_configs, selected_metrics, session_id):
    server_storage.insert(session_id, "Configs", selected_configs)
    server_storage.insert(session_id, "Metrics", selected_metrics)
    return html.Div("")

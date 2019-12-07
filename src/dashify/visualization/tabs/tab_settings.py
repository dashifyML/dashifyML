import dash_html_components as html
from typing import List
from dash.dependencies import Input, Output
import dash_core_components as dcc
from dashify.visualization.app import app
from dashify.visualization.data_model.cache import cache
import dash_table
import pandas as pd


def render_settings(session_id: str, log_dir):
    config_settings_dict = cache.get_configs_settings(session_id)
    params = data_table.get_config_columns()
    config_settings = create_configs_settings(session_id, params)
    metrics_keys = data_table.get_metrics_columns()
    metrics_settings_table = create_metrics_settings_table(session_id, metrics_keys, params)
    content = html.Div(
        children=[html.H3("What to track?"), html.Div([config_settings, metrics_settings_table], className="row")])
    return content


def create_configs_settings(session_id: str, keys: List[str]):
    settings_type = "Configs"
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


def create_metrics_settings_table(session_id: str, metrics_keys: List[str], config_params: List[str]):
    settings_type = "Metrics"
    agg_fun_list = ["min", "mean", "max"]
    df_metrics_settings = server_storage.get(session_id, settings_type)
    if df_metrics_settings is None:
        df_metrics_settings = pd.DataFrame.from_dict({"metrics": metrics_keys})
        df_metrics_settings["Selected"] = "y"
        df_metrics_settings["Aggregation"] = agg_fun_list[0]
        df_metrics_settings["Std_band"] = "n"
        df_metrics_settings["Grouping parameter"] = config_params[0] if config_params else None

    table = html.Div([
            html.H5("Metrics"),
            dash_table.DataTable(
                id='table-metrics',
                data=df_metrics_settings.to_dict('records'),
                columns=[
                    {'id': 'metrics', 'name': 'metrics'},
                    {'id': 'Selected', 'name': 'Selected', 'presentation': 'dropdown'},
                    {'id': 'Aggregation', 'name': 'Aggregation', 'presentation': 'dropdown'},
                    {'id': 'Std_band', 'name': 'Std_band', 'presentation': 'dropdown'},
                    {'id': 'Grouping parameter', 'name': 'Grouping parameter', 'presentation': 'dropdown'},
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
                    },
                    'Std_band': {
                        'options': [
                            {'label': i, 'value': i}
                            for i in ["y", "n"]
                        ]
                    },
                    'Grouping parameter': {
                        'options': [
                            {'label': i, 'value': i}
                            for i in config_params
                        ]
                    }
                }
            ),
            html.Div(id='table-dropdown-container')
        ], className="five columns"
    )
    return table


@app.callback(
    Output('hidden-div-placeholder', "children"),
    [Input('Configs', "value"), Input("session-id", "children"), Input('table-metrics', 'data'), Input('table-metrics', 'columns')])
def settings_callback(selected_configs, session_id, metric_rows, metric_colums):
    # store config
    server_storage.insert(session_id, "Configs", selected_configs)
    # store metrics
    df = pd.DataFrame(metric_rows, columns=[c['name'] for c in metric_colums])
    server_storage.insert(session_id, "Metrics", df)
    return html.Div("")

import dash_html_components as html
import dash_core_components as dcc
from dashify.visualization.controllers.data_controllers import MetricsController, ConfigController, GridSearchController
import dash_table
from dash.dependencies import Input, Output
from dashify.visualization.app import app
import pandas as pd
from dash import no_update
from flask import url_for
import flask


def render_settings(session_id: str):
    gs_dropdown = create_grid_search_dropdown(session_id)
    config_settings = html.Div(children=[create_configs_settings(session_id)], id="configs-wrapper")
    metrics_settings_table =  html.Div(children=[create_metrics_settings_table(session_id)], id="metrics-wrapper")
    log_dir_div = html.Div(children=f"analyzing {GridSearchController.get_log_dir()}", id="log-dir")
    log_dir_row = html.Div(children=[log_dir_div, gs_dropdown])
    content = html.Div(children=[html.Div([html.H3("What to track?"), log_dir_row], className="row"),
                                 html.Div([config_settings, metrics_settings_table], className="row", id="configs-metrics-row")]
                       )
    return content


def create_grid_search_dropdown(session_id: str):
    gridsearch_ids = GridSearchController.get_gridsearch_ids()
    active_gridsearch_id = GridSearchController.get_activated_grid_search_id(session_id)
    return dcc.Dropdown(options=[{'label': gridsearch_id, 'value': gridsearch_id} for gridsearch_id in gridsearch_ids],
                        value=active_gridsearch_id,
                        id="gs-dropdown")


def create_configs_settings(session_id: str):
    options = [{'label': key, 'value': key} for key in sorted(ConfigController.get_configs_settings(session_id))]
    selected_elements = ConfigController.get_selected_configs_settings(session_id)
    settings = html.Div(
        children=[html.H5("Configs"),
                  dcc.Checklist(
                      options=options,
                      value=selected_elements,
                      id="Configs"
                  )],
        className="three columns"
    )
    return settings


def create_metrics_settings_table(session_id: str):
    agg_fun_list = ["min", "mean", "max", "first", "last"]
    df_metrics_settings = MetricsController.get_metrics_settings(session_id)
    df_metrics_settings = df_metrics_settings.sort_values(by=["metrics"])
    selected_configs = ConfigController.get_selected_configs_settings(session_id)
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
                {'id': 'Grouping parameter 1', 'name': 'Grouping parameter 1', 'presentation': 'dropdown'},
                {'id': 'Grouping parameter 2', 'name': 'Grouping parameter 2', 'presentation': 'dropdown'},
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
                'Grouping parameter 1': {
                    'options': [
                        {'label': i, 'value': i}
                        for i in sorted(selected_configs)
                    ]
                },
                'Grouping parameter 2': {
                    'options': [
                        {'label': i, 'value': i}
                        for i in ["None"] + sorted(selected_configs)
                    ]
                }
            }
        ),
        html.Div(id='table-dropdown-container')
    ], className="six columns"
    )
    return table


@app.callback(
    Output('configs-wrapper', 'children'),
    [Input("session-id", "children"), Input('gs-dropdown', 'value')])
def update_config_callback(session_id, grid_search_id):
    # store selected grid search id
    if grid_search_id is not None:
        GridSearchController.set_activated_grid_search_id(session_id, grid_search_id)
        config_content = create_configs_settings(session_id)
        return config_content
    return no_update

@app.callback(
    Output('metrics-wrapper', 'children'),
    [Input("session-id", "children"), Input('gs-dropdown', 'value')])
def update_metrics_callback(session_id, grid_search_id):
    # store selected grid search id
    if grid_search_id is not None:
        GridSearchController.set_activated_grid_search_id(session_id, grid_search_id)   # TODO this is updated in update_config_callback as well...
        metrics_content = create_metrics_settings_table(session_id)
        return metrics_content
    return no_update


@app.callback(
    Output('hidden-div-placeholder', "children"),
    [Input('Configs', "value"), Input("session-id", "children"), Input('table-metrics', 'data'),
     Input('table-metrics', 'columns')])
def settings_callback(selected_configs, session_id, metric_rows, metric_colums):
    # store config
    ConfigController.set_selected_configs_settings(session_id, selected_configs)
    # store metrics
    df = pd.DataFrame(metric_rows, columns=[c['name'] for c in metric_colums])
    MetricsController.set_metrics_settings(session_id, df)
    return html.Div("")

@app.callback(
    Output('download-analysis-link', "href"),
    [Input("session-id", "children"), Input('gs-dropdown', 'value')])
def update_download_link(session_id, grid_search_id):
    url = url_for("download_analysis_data")
    return url

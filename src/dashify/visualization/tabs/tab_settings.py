import dash_html_components as html
import dash_core_components as dcc
from dashify.visualization.data_controllers import MetricsController, ConfigController
import dash_table
from dash.dependencies import Input, Output
from dashify.visualization.app import app
import pandas as pd


def render_settings(gs_log_dir: str, session_id: str):
    config_settings = create_configs_settings(gs_log_dir, session_id)
    metrics_settings_table = create_metrics_settings_table(gs_log_dir, session_id)
    content = html.Div(
        children=[html.H3("What to track?"), html.Div([config_settings, metrics_settings_table], className="row")])
    return content


def create_configs_settings(gs_log_dir: str, session_id: str):
    options = [{'label': key, 'value': key} for key in ConfigController.get_configs_settings(gs_log_dir, session_id)]
    selected_elements = ConfigController.get_selected_configs_settings(gs_log_dir, session_id)
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


def create_metrics_settings_table(gs_log_dir: str, session_id: str):
    agg_fun_list = ["min", "mean", "max"]
    df_metrics_settings = MetricsController.get_metrics_settings(gs_log_dir, session_id)

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
                        for i in ConfigController.get_selected_configs_settings(gs_log_dir, session_id)
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
    [Input('Configs', "value"), Input("session-id", "children"), Input('table-metrics', 'data'),
     Input('table-metrics', 'columns'), Input("hidden-log-dir", "children"),])
def settings_callback(selected_configs, session_id, metric_rows, metric_colums, gs_log_dir):
    # store config
    ConfigController.set_selected_configs_settings(gs_log_dir, session_id, selected_configs)
    # store metrics
    df = pd.DataFrame(metric_rows, columns=[c['name'] for c in metric_colums])
    MetricsController.set_metrics_settings(gs_log_dir, session_id, df)
    return html.Div("")

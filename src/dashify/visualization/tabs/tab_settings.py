from dashify.data_import.data_table import DataTable
from dashify.data_import.data_reader import GridSearchLoader
from dashify.visualization import Settings
import dash_html_components as html
from typing import List
from dash.dependencies import Input, Output
import dash_core_components as dcc
from dashify.visualization.app import app
from dashify.visualization.storage.in_memory import server_storage


gs_loader = GridSearchLoader(Settings.log_dir)
data_table = DataTable(gs_loader)


def render_settings(session_id: str):
    config_settings = create_settings(session_id, data_table.get_config_columns(), "Configs")
    metrics_settings = create_settings(session_id, data_table.get_metrics_columns(), "Metrics")
    content = html.Div(children=[html.H3("What to track?"), html.Div(children=[config_settings, metrics_settings], className="row")])
    return content


def create_settings(session_id:str, keys: List[str], settings_type: str):
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


@app.callback(
    Output('hidden-div-placeholder', "children"),
    [Input('Configs', "value"), Input('Metrics', "value"), Input("session-id", "children")])
def settings_callback(selected_configs, selected_metrics, session_id):
    server_storage.insert(session_id, "Configs", selected_configs)
    server_storage.insert(session_id, "Metrics", selected_metrics)
    return html.Div("")

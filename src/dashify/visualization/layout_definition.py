import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dashify.visualization.tabs.tab_graph_grids import render_graphs
from dashify.visualization.tabs.tab_experiments_table import render_table
from dashify.visualization.tabs.tab_settings import render_settings
from dashify.visualization.app import app
import uuid
from dashify.visualization.controllers.data_controllers import GridSearchController
import flask
from flask import url_for

def get_layout(gs_log_dir, session_id):
    tabs = dcc.Tabs(id="tabs", value='tab-graphs', children=[
        dcc.Tab(label='Visualization', value='tab-graphs', id="tab-button-graphs"),
        dcc.Tab(label='Experiments', value='tab-table', id="tab-button-table"),
        dcc.Tab(label='Configuration', value='tab-settings', id="tab-button-settings")
    ], )
    title_row = html.Div(children=[html.Img(src='/assets/img/dashify_logo_2_scaled.png', id="dashify-logo"), tabs],
                         id="title-row")
    hidde_log_dir = html.Div(children=f"{gs_log_dir}", id="hidden-log-dir", style={'display': 'none'})

    layout = html.Div(children=[title_row,
                                hidde_log_dir,
                                html.Div(id='tabs-content'),
                                # super ugly for session ids... but Dash wants it that way.
                                # https://dash.plot.ly/sharing-data-between-callbackstab_gridsearch_table
                                html.Div(session_id, id='session-id', style={'display': 'none'}),
                                # yet another ugly hack since callbacks always need an output defined...
                                html.Div(id="hidden-div-placeholder", style={"display": "none"}),
                                html.Div(id="hidden-div-placeholder-2", style={"display": "none"})
                                ])
    return layout


def render_download_button(button_id, button_text, file_name, href=None):
    return html.Div([
        html.Br(),
        html.A(html.Button(button_text),
               id=button_id,
               download=file_name,
               href=href,
               style={"display": "inline-block"})
    ], style={"text-align": "center"})


@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value'), Input("session-id", "children"), Input("hidden-log-dir", "children")])
def render_content(tab, session_id, log_dir):
    if GridSearchController.get_log_dir() is None:
        GridSearchController.set_log_dir(log_dir)

    # set session_id in flask's session
    flask.session["session_id"] = session_id

    if tab == 'tab-settings':
        return html.Div([
            render_settings(session_id),
            render_download_button("download-analysis-link", "Download Analysis as .json", "analysis.json", url_for("download_analysis_data")),
        ])
    elif tab == 'tab-table':
        return html.Div([
            render_table(session_id),
            render_download_button("download-exp-link", "Download as .csv", "experiments_data.csv")
        ])
    elif tab == 'tab-graphs':
        return html.Div(children=render_graphs(session_id))

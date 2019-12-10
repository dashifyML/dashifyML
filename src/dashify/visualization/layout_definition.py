import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dashify.visualization.tabs.tab_graph_grids import render_graphs
from dashify.visualization.tabs.tab_experiments_table import render_table
from dashify.visualization.tabs.tab_settings import render_settings
from dashify.visualization.app import app
import uuid


def get_layout(gs_log_dir):
    layout = html.Div(children=[
        html.H1(children='D-a-s-h-i-f-y'),

        html.Div(children=f"analyzing {gs_log_dir}", id="log-dir"),
        html.Div(children=f"{gs_log_dir}", id="hidden-log-dir", style={'display': 'none'}),

        dcc.Tabs(id="tabs", value='tabs', children=[
            dcc.Tab(label='Settings', value='tab-settings'),
            dcc.Tab(label='Table', value='tab-table'),
            dcc.Tab(label='Graphs', value='tab-graphs'),
        ]),
        html.Div(id='tabs-content'),
        # super ugly for session ids... but Dash wants it that way.
        # https://dash.plot.ly/sharing-data-between-callbackstab_gridsearch_table
        html.Div(str(uuid.uuid4()), id='session-id', style={'display': 'none'}),
        # yet another ugly hack since callbacks always need an output defined...
        html.Div(id="hidden-div-placeholder", style={"display":"none"}),
        html.Div(id="hidden-div-placeholder-2", style={"display":"none"})
    ])
    return layout


def get_gs_log_dir(layout):
    return layout.children[2].children


@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value'), Input("session-id", "children"), Input("hidden-log-dir", "children")])
def render_content(tab, session_id, gs_log_dir):
    if tab == 'tab-settings':
        return html.Div([
            render_settings(gs_log_dir, session_id)
        ])
    elif tab == 'tab-table':
        return html.Div([
            render_table(gs_log_dir, session_id)
        ])
    elif tab == 'tab-graphs':
        return html.Div(children=render_graphs(gs_log_dir, session_id), id="graph-grids")






import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dashify.visualization.tabs.tab_graph_grids import render_graphs
from dashify.visualization import Settings
from dashify.visualization.tabs.tab_gridsearch_table import render_table
from dashify.visualization.tabs.tab_settings import render_settings
from dashify.visualization.app import app
import uuid

layout = html.Div(children=[
    html.H1(children='D-a-s-h-i-f-y'),

    html.Div(children=f"analyzing {Settings.log_dir}", id="log-dir"),

    dcc.Tabs(id="tabs", value='tabs', children=[
        dcc.Tab(label='Settings', value='tab-settings'),
        dcc.Tab(label='Table', value='tab-table'),
        dcc.Tab(label='Graphs', value='tab-graphs'),
    ]),
    html.Div(id='tabs-content'),
    # super ugly for session ids... but Dash wants it that way.
    # https://dash.plot.ly/sharing-data-between-callbacks
    html.Div(str(uuid.uuid4()), id='session-id', style={'display': 'none'}),
    # yet another ugly hack since callbacks always need an output defined...
    html.Div(id="hidden-div-placeholder", style={"display":"none"})
])


@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value'), Input("session-id", "children")])
def render_content(tab, session_id):
    if tab == 'tab-settings':
        return html.Div([
            render_settings(session_id)
        ])
    elif tab == 'tab-table':
        return html.Div([
            render_table(session_id)
        ])
    elif tab == 'tab-graphs':
        return html.Div(children=render_graphs(Settings.log_dir), id="graph-grids")

# TABLE TAB STUFF






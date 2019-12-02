import dash_html_components as html
from dash.dependencies import Input, Output
from dashify.visualization.app import app
from dashify.visualization.tabs.tab_graph_grids import render_graphs
from dashify.visualization import Settings
from dashify.visualization.tabs.tab_gridsearch_table import render_table
from dashify.visualization.tabs.tab_settings import render_settings

# @app.callback(Output('tabs-content', 'children'),
#               [Input('tabs', 'value'), Input("session-id", "children")])
# def render_content(tab, session_id):
#     if tab == 'tab-settings':
#         return html.Div([
#             render_settings(session_id)
#         ])
#     elif tab == 'tab-table':
#         return html.Div([
#             render_table()
#         ])
#     elif tab == 'tab-graphs':
#         return html.Div(children=render_graphs(Settings.log_dir), id="graph-grids")
#
#

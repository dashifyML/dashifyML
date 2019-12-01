import dash_html_components as html
from dash.dependencies import Input, Output
from dashify.visualization.layout_definition import app
from dashify.visualization.graph_grids import render_graphs
from dashify.visualization import Settings
from dashify.visualization.gridsearch_table import render_table

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-settings':
        return html.Div([
            html.H3('Settings')
        ])
    elif tab == 'tab-table':
        return html.Div([
            render_table()
        ])
    elif tab == 'tab-graphs':
        return html.Div(children=render_graphs(Settings.log_dir), id="graph-grids")



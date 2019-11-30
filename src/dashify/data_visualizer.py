import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
from dashify.data_reader import GridSearchLoader, Experiment
import argparse
from typing import List, Dict


def create_app(graphs: List[dcc.Graph], log_dir: str):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div(children=[
        html.H1(children='Dashify'),

        html.Div(children=f"analyzing {log_dir}"),
        html.Div(create_collapsable_elements(graphs), style={"width": "100%"})
    ])
    return app


# LAYOUT STUFF

def collapsable_item(button_text: str, graph_grid):
    # we use this function to make the example items to avoid code duplication
    return dbc.Card(
        [
            # group header
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        button_text,
                        color="link",
                        id=f"{button_text}-group-toggle",
                    )
                )
            ),
            # group content
            dbc.Collapse(
                dbc.CardBody(graph_grid),
                id=f"collapse-{button_text}",
            ),
        ]
    )


def create_collapsable_elements(graph_grid_dict: Dict[str, List[dcc.Graph]]):
    return [collapsable_item(key, grid) for key, grid in graph_grid_dict.items()]


def create_graph_grid(graphs) -> Dict[str, List[dcc.Graph]]:
    # get the dataset split type from each graph
    split_type_of_graphs = [os.path.dirname(g.id) for g in graphs]

    # create a dictionary to seperate the graphs based on the split type
    graph_dict = {split_type: [] for split_type in set(split_type_of_graphs)}
    for id, split_type in enumerate(split_type_of_graphs):
        graph_dict[split_type].append(graphs[id])

    return [collapsable_item(key, graphs) for key, graphs in graph_dict.items()]


# @app.callback(
#     [Output(f"collapse-{i}", "is_open") for i in range(1, 4)],
#     [Input(f"group-{i}-toggle", "n_clicks") for i in range(1, 4)],
#     [State(f"collapse-{i}", "is_open") for i in range(1, 4)],
# )
# def toggle_accordion(n1, n2, n3, is_open1, is_open2, is_open3):
#     ctx = dash.callback_context
#
#     if not ctx.triggered:
#         return ""
#     else:
#         button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#
#     if button_id == "group-1-toggle" and n1:
#         return not is_open1, False, False
#     elif button_id == "group-2-toggle" and n2:
#         return False, not is_open2, False
#     elif button_id == "group-3-toggle" and n3:
#         return False, False, not is_open3
#     return False, False, False


def create_graph_grid(graphs: List[dcc.Graph], num_cols=3):
    def create_element(graph, i):
        return html.Div([
            graph
        ], className="three columns", style={"width": "30%"})

    elements = [create_element(graph, i) for i, graph in enumerate(graphs)]
    rows = []
    row = []
    for i, element in enumerate(elements):
        if i % num_cols == 0 and i > 0:
            rows.append(html.Div(row, className="row"))
            row = []
        row.append(element)
    if row:
        rows.append(html.Div(row, className="row"))

    return html.Div(rows)


# GRAPH STUFF

def create_graphs(gs_loader: GridSearchLoader) -> List[dcc.Graph]:
    metric_tags = gs_loader.get_experiment(gs_loader.get_experiment_ids()[0]).metrics.keys()
    return [create_graph(metric_tag, gs_loader) for metric_tag in metric_tags]


def create_graph(metric_tag: str, gs_loader: GridSearchLoader) -> dcc.Graph:
    def prepare_single_data_series(experiment: Experiment, metric_tag: str) -> Dict:
        y = experiment.metrics[metric_tag]
        series = {"x": list(range(len(y))), 'y': y, 'type': 'linear', 'name': experiment.identifier}
        return series

    def prepare_data(metric_tag: str, gs_loader: GridSearchLoader) -> List:
        experiment_ids = gs_loader.get_experiment_ids()
        return [prepare_single_data_series(gs_loader.get_experiment(experiment_id), metric_tag=metric_tag) for
                experiment_id in experiment_ids]

    g = dcc.Graph(
        id=metric_tag,
        figure={
            'data': prepare_data(metric_tag, gs_loader),
            'layout': {
                'title': metric_tag
            }
        }
    )

    return g


def parse_args():
    parser = argparse.ArgumentParser(description='Visualize grid search experiments')
    parser.add_argument('--logdir', type=str, help='Path tho the grid search root directory')
    args = parser.parse_args()
    log_dir = args.logdir
    if log_dir is None:
        raise Exception("Please speficy the log dir with --logdir <your grid search log dir>")
    else:
        return log_dir


if __name__ == '__main__':
    log_dir = parse_args()

    gs_loader = GridSearchLoader(log_dir)
    graphs = create_graphs(gs_loader)
    app = create_app(graphs, log_dir)
    app.run_server(debug=True)

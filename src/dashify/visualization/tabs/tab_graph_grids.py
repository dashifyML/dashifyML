import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import os
from dashify.data_import.data_reader import GridSearchLoader, Experiment
from typing import List, Dict
import operator
from functools import reduce
from dashify.visualization import Settings


def render_graphs(log_dir: str):
    gs_loader = GridSearchLoader(log_dir)
    graphs = create_graphs(gs_loader)
    graph_groups = create_graph_groups(graphs)
    grids = create_grids(graph_groups)

    interval = dcc.Interval(
        id='graph-interval-component',
        interval=10*1000,  # in milliseconds
        n_intervals=0
    )
    grids.append(interval)
    return grids


def create_grids(graph_groups: Dict[str, List[dcc.Graph]], num_cols=3):
    grids = [create_html_graph_grid_from_group(graph_group, num_cols=num_cols) for key, graph_group in graph_groups.items()]
    headlines = [html.H4(key.upper()) for key in graph_groups.keys()]
    tab_content = list(reduce(operator.add, zip(headlines, grids)))
    return tab_content


# @app.callback(Output('graph-grids', 'children'),
#               [Input('graph-interval-component', 'n_intervals')])
# def update_metrics(n):
#     return render_graphs(Settings.log_dir)


def create_html_graph_grid_from_group(graph_group: List[dcc.Graph], num_cols=3) -> html.Div:
    def create_element(graph, i):
        return html.Div([
            graph
        ], className="three columns", style={"width": "30%"})

    elements = [create_element(graph, i) for i, graph in enumerate(graph_group)]
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
# we combine all the measurements based on the metric keys
# we then combine the graphs to groups based on the dataset split (part of metric key)

def create_graph_groups(graphs: List[dcc.Graph], split_fun=None) -> Dict[str, List[dcc.Graph]]:
    # get the dataset split type from each graph
    if split_fun is None:
        split_fun = os.path.dirname
    split_type_of_graphs = [split_fun(g.id) for g in graphs]

    # create a dictionary to seperate the graphs based on the split type
    graph_dict = {split_type: [] for split_type in set(split_type_of_graphs)}
    for id, split_type in enumerate(split_type_of_graphs):
        graph_dict[split_type].append(graphs[id])

    return graph_dict


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
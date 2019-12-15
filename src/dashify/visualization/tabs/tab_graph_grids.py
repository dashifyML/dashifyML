import dash_html_components as html
import os
from typing import List, Dict
import operator
from dashify.aggregation.aggregator import DataAggregator
from functools import reduce
from dashify.visualization.app import app
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dashify.visualization.controllers.data_controllers import GraphController, MetricsController, ExperimentController
from dashify.visualization.plotting.utils import generate_marks, get_band_graph, get_line_graph
from tqdm import tqdm
import multiprocessing as mp
from itertools import repeat


def render_graphs(session_id: str):
    graphs = create_graphs(session_id)
    graph_groups = create_graph_groups(graphs)
    graph_content = html.Div(children=create_grids(graph_groups), id="graph-content")

    interval = dcc.Interval(
        id='graph-interval-component',
        interval=1000 * 1000,  # in milliseconds
        n_intervals=0
    )

    # Slider for smoothing
    graph_settings = [
        html.H4("Graph Settings"),
        html.P("Smoothing"),
        html.Div(
            children=[dcc.Slider(
                id="smoothing-slider",
                min=0,
                max=1,
                value=GraphController.get_smoothing_factor(session_id),
                step=1e-2,
                marks=generate_marks(0, 1, 0.2),
            )], style={"width": "30%"}
        )
    ]
    tab_content = html.Div(children=[*graph_settings, graph_content, interval])
    return tab_content


def create_grids(graph_groups: Dict[str, List[dcc.Graph]], num_cols=3):
    grids = [create_html_graph_grid_from_group(graph_group, num_cols=num_cols) for key, graph_group in
             graph_groups.items()]
    headlines = [html.H4(key.upper()) for key in graph_groups.keys()]
    if grids:
        tab_content = list(reduce(operator.add, zip(headlines, grids)))
    else:
        tab_content = headlines
    return tab_content


# @app.callback(Output('graph-grids', 'children'),
#               [Input('graph-interval-component', 'n_intervals')])
# def update_metrics(n):
#     return render_graphs(Settings.gs_log_dir)


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


def create_graph_by_selection(session_id, metric_tag):
    graph = create_graph_with_bands(session_id, metric_tag) if MetricsController.is_band_enabled_for_metric(session_id, metric_tag) \
        else create_graph_with_line_plot(session_id, metric_tag)
    return graph


def create_graphs(session_id: str) -> List[dcc.Graph]:
    metric_tags = MetricsController.get_selected_metrics(session_id)

    # refresh the data once
    ExperimentController.refresh(session_id)

    pool = mp.Pool(processes=mp.cpu_count())
    graphs = pool.starmap(create_graph_by_selection, zip(repeat(session_id, len(metric_tags)), metric_tags))
    pool.close()
    return graphs


def create_graph_with_line_plot(session_id: str, metric_tag: str) -> dcc.Graph:
    smoothing = GraphController.get_smoothing_factor(session_id)
    experiment_ids = ExperimentController.get_experiment_ids(session_id)
    metric_data = ExperimentController.get_experiment_data_by_experiment_id(session_id, experiment_ids, [metric_tag])

    def prepare_single_data_series(experiment_id: str) -> Dict:
        data = metric_data[metric_data["experiment_id"] == experiment_id][metric_tag].values[0]
        data = data if isinstance(data, list) else []
        data = DataAggregator.smooth(data, smoothing)
        dict_data = {
            "experiment_id": experiment_id,
            "data": data
        }
        return dict_data

    series = []
    for experiment_id in tqdm(experiment_ids):
        series.append(prepare_single_data_series(experiment_id))

    line_graph = get_line_graph(id=metric_tag, series=series, title=metric_tag)
    return line_graph


def create_graph_with_bands(session_id: str, metric_tag: str) -> dcc.Graph:
    smoothing = GraphController.get_smoothing_factor(session_id)
    group_by_param = MetricsController.get_metric_setting_by_metric_tag(session_id, metric_tag, "Grouping parameter")
    experiment_ids = ExperimentController.get_experiment_ids(session_id)
    metric_data_df = ExperimentController.get_experiment_data_by_experiment_id(session_id, experiment_ids)

    def prepare_data(metric_tag: str) -> Dict:
        aggregator = DataAggregator(experiments_df=metric_data_df, smoothing=smoothing)
        data = aggregator.group_by_param(metric_tag, group_by_param)
        return data

    # aggregate data and get band graph
    data_groups = prepare_data(metric_tag)
    band_graph = get_band_graph(id=metric_tag, series_groups=data_groups, title=metric_tag)
    return band_graph


@app.callback(
    Output('graph-content', "children"),
    [Input("session-id", "children"), Input('smoothing-slider', 'value'), Input('graph-interval-component', 'n_intervals')])
def settings_callback(session_id, smoothing, interval):
    GraphController.set_smoothing_factor(session_id, smoothing)
    graphs = create_graphs(session_id)
    graph_groups = create_graph_groups(graphs)
    return create_grids(graph_groups)

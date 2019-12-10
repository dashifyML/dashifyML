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


def render_graphs(gs_log_dir: str, session_id: str):
    smoothing_weight = GraphController.get_smoothing_factor(gs_log_dir, session_id)
    graphs = create_graphs(gs_log_dir, session_id)
    graph_groups = create_graph_groups(graphs)
    grids = create_grids(graph_groups)

    interval = dcc.Interval(
        id='graph-interval-component',
        interval=10 * 1000,  # in milliseconds
        n_intervals=0
    )
    grids.append(interval)

    # Slider for smoothing
    graph_settings = [
        html.H4("Graph Settings"),
        html.P("Smoothing"),
        html.Div(
            children=[dcc.Slider(
                id="smoothing-slider",
                min=0,
                max=1,
                value=smoothing_weight,
                step=1e-2,
                marks=generate_marks(0, 1, 0.2),
            )], style={"width": "30%"}
        )

    ]
    grids = graph_settings + grids
    return grids


def create_grids(graph_groups: Dict[str, List[dcc.Graph]], num_cols=3):
    grids = [create_html_graph_grid_from_group(graph_group, num_cols=num_cols) for key, graph_group in
             graph_groups.items()]
    headlines = [html.H4(key.upper()) for key in graph_groups.keys()]
    tab_content = list(reduce(operator.add, zip(headlines, grids)))
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


def create_graphs(gs_log_dir: str, session_id: str) -> List[dcc.Graph]:
    metric_tags = MetricsController.get_selected_metrics(gs_log_dir, session_id)

    return [
        create_graph_with_bands(gs_log_dir, session_id, metric_tag)
        if MetricsController.is_band_enabled_for_metric(gs_log_dir, session_id, metric_tag)
        else create_graph_with_line_plot(gs_log_dir, session_id, metric_tag) for metric_tag in metric_tags]


def create_graph_with_line_plot(gs_log_dir: str, session_id: str, metric_tag: str) -> dcc.Graph:
    smoothing = GraphController.get_smoothing_factor(gs_log_dir, session_id)

    def prepare_single_data_series(experiment_id: str, metric_tag: str) -> Dict:
        # TBD: can create a controller
        data = ExperimentController.get_experiment_data_by_experiment_id(gs_log_dir, session_id, experiment_id, metric_tag)
        data = DataAggregator.smooth(data, smoothing)
        dict_data = {
            "experiment_id": experiment_id,
            "data": data
        }
        return dict_data

    series = []
    experiment_ids = ExperimentController.get_experiment_ids(gs_log_dir, session_id)
    for experiment_id in experiment_ids:
        series.append(prepare_single_data_series(experiment_id, metric_tag))

    line_graph = get_line_graph(id=metric_tag, series=series, title=metric_tag)
    return line_graph


def create_graph_with_bands(gs_log_dir: str, session_id: str, metric_tag: str) -> dcc.Graph:
    smoothing = GraphController.get_smoothing_factor(gs_log_dir, session_id)
    group_by_param = MetricsController.get_metric_setting_by_metric_tag(gs_log_dir, session_id, metric_tag, "Grouping parameter")

    def prepare_data(metric_tag: str) -> Dict:
        experiment_ids = ExperimentController.get_experiment_ids(gs_log_dir, session_id)
        exps = [ExperimentController.get_experiment_data_by_experiment_id(gs_log_dir, session_id, exp_id)
                for exp_id in experiment_ids]
        aggregator = DataAggregator(experiments_df=exps, smoothing=smoothing)
        data = aggregator.group_by_param(metric_tag, group_by_param)
        return data

    # aggregate data and get band graph
    data_groups = prepare_data(metric_tag)
    band_graph = get_band_graph(id=metric_tag, series_groups=data_groups, title=metric_tag)
    return band_graph


@app.callback(
    Output('hidden-div-placeholder-2', "children"),
    [Input("session-id", "children"), Input('smoothing-slider', 'value'), Input("hidden-log-dir", "children")])
def settings_callback(session_id, smoothing, gs_log_dir):
    GraphController.set_smoothing_factor(gs_log_dir, session_id, smoothing)
    return html.Div("")

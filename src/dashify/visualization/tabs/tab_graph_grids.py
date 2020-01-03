import dash_html_components as html
import os
from typing import List, Dict
import operator
from functools import reduce
from dashify.visualization.app import app
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dashify.visualization.controllers.data_controllers import GraphController, MetricsController, ExperimentController
from dashify.visualization.plotting.utils import generate_marks, get_band_graph, get_line_graph
import multiprocessing as mp
from itertools import repeat
from dashify.visualization import layout_definition
from flask import url_for
from dashify.metrics.processor import MetricDataProcessor
import flask

def render_graphs(session_id: str):
    # graphs
    graphs = create_graphs(session_id)
    graph_groups = create_graph_groups(graphs)
    graph_content = html.Div(children=create_grids(session_id, graph_groups), id="graph-content")

    # other layout elements
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


def create_grids(session_id: str, graph_groups: Dict[str, List[dcc.Graph]], num_cols=3):
    grids = [create_html_graph_grid_from_group(session_id, graph_group, num_cols=num_cols) for key, graph_group in
             graph_groups.items()]
    headlines = [html.H4(key.upper()) for key in graph_groups.keys()]
    if grids:
        tab_content = list(reduce(operator.add, zip(headlines, grids)))
    else:
        tab_content = headlines
    return tab_content


def create_html_graph_grid_from_group(session_id: str, graph_group: List[dcc.Graph], num_cols=3) -> html.Div:
    def build_download_url(metric_tag):
        to_aggregate = MetricsController.is_band_enabled_for_metric(session_id, metric_tag)
        return url_for("download_graph_data", session_id=session_id, metric_tag=metric_tag, aggregate=to_aggregate)

    def create_element(graph):
        button_id = f"download-data-{graph.id}"

        return html.Div([
            graph,
            layout_definition.render_download_button(button_text="Download as .json",
                                                     button_id=button_id,
                                                     href=build_download_url(graph.id),
                                                     file_name=f"{graph.id}.json")
        ], className="three columns", style={"width": "30%"})

    elements = [create_element(graph) for graph_id, graph in enumerate(graph_group)]
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
    series = MetricDataProcessor.get_data(session_id, metric_tag)
    line_graph = get_line_graph(id=metric_tag, series=series, title=metric_tag)
    return line_graph


def create_graph_with_bands(session_id: str, metric_tag: str) -> dcc.Graph:
    data_groups = MetricDataProcessor.get_aggregated_data(session_id, metric_tag)
    band_graph = get_band_graph(id=metric_tag, series_groups=data_groups, title=metric_tag)
    return band_graph


@app.callback(
    Output('graph-content', "children"),
    [Input("session-id", "children"), Input('smoothing-slider', 'value'),
     Input('graph-interval-component', 'n_intervals')]
)
def settings_callback(session_id, smoothing, interval):
    GraphController.set_smoothing_factor(session_id, smoothing)
    graphs = create_graphs(session_id)
    graph_groups = create_graph_groups(graphs)
    return create_grids(session_id, graph_groups)
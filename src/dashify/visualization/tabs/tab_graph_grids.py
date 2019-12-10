import dash_html_components as html
import os
from typing import List, Dict
import operator
import numpy as np
import plotly.graph_objs as go
from pandas import DataFrame
from dashify.aggregation.aggregator import DataAggregator
from functools import reduce
from plotly.colors import DEFAULT_PLOTLY_COLORS
from dashify.visualization.app import app
import dash_core_components as dcc
from dash.dependencies import Input, Output
from dashify.visualization.controllers.data_controllers import GraphController, MetricsController, ExperimentController


def gen_marks(min, max, step):
    marks = {}
    for i in np.arange(min, max + 1, step):
        if i % max == 0:
            marks[int(i)] = str(round(i, 2))
        else:
            marks[i] = str(round(i, 2))
    return marks


def get_selected_smoothing(gs_log_dir, session_id):
    smoothing = GraphController.get_smoothing_factor(gs_log_dir, session_id)
    smoothing = 0.0 if smoothing is None else smoothing
    return smoothing


def render_graphs(gs_log_dir: str, session_id: str):
    # get smoothing weight
    smoothing = get_selected_smoothing(gs_log_dir, session_id)

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
                value=smoothing,
                step=1e-2,
                marks=gen_marks(0, 1, 0.2),
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


def get_selected_param(gs_log_dir, session_id, metric_tag):
    return str(MetricsController.get_metric_setting_by_metric_tag(gs_log_dir, session_id, metric_tag, ["Grouping parameter"]).iloc[0].values[0])


def is_std_selected(gs_log_dir, session_id, metric_tag):
    settings_df = MetricsController.filter_metrics_settings(gs_log_dir, session_id, "Std_band", "y")
    settings_df = settings_df[settings_df["metrics"] == metric_tag]
    return settings_df.shape[0] > 0


def create_graphs(gs_log_dir: str, session_id: str) -> List[dcc.Graph]:
    metric_tags = MetricsController.get_selected_metrics(gs_log_dir, session_id)

    return [
        create_graph_with_std(gs_log_dir, session_id, metric_tag)
        if is_std_selected(gs_log_dir, session_id, metric_tag)
        else create_graph_with_line_plot(gs_log_dir, session_id, metric_tag) for metric_tag in metric_tags]


def create_graph_with_line_plot(gs_log_dir: str, session_id: str, metric_tag: str) -> dcc.Graph:
    # get smoothing factor
    smoothing = get_selected_smoothing(gs_log_dir, session_id)

    def prepare_single_data_series(experiment_id: str, metric_tag: str) -> Dict:
        y = ExperimentController.get_experiment_data_by_experiment_id(gs_log_dir, session_id, experiment_id)
        y = y[metric_tag].iloc[0]
        y = DataAggregator.smooth(y, smoothing)

        series = {"x": list(range(len(y))), 'y': y, 'type': 'linear', 'name': experiment_id}
        return series

    def prepare_data(metric_tag: str) -> List:
        experiment_ids = ExperimentController.get_experiment_ids(gs_log_dir, session_id)
        return [prepare_single_data_series(experiment_id=experiment_id,
                                           metric_tag=metric_tag)
                for experiment_id in experiment_ids]

    g = dcc.Graph(
        id=metric_tag,
        figure={
            'data': prepare_data(metric_tag),
            'layout': {
                'title': metric_tag,
            }
        }
    )
    return g


def create_graph_with_std(gs_log_dir: str, session_id: str, metric_tag: str) -> dcc.Graph:
    # get smoothing factor
    smoothing = get_selected_smoothing(gs_log_dir, session_id)

    # group by param
    group_by_param = get_selected_param(gs_log_dir, session_id, metric_tag)

    def prepare_data(metric_tag: str) -> List:
        experiment_ids = ExperimentController.get_experiment_ids(gs_log_dir, session_id)
        exps = [ExperimentController.get_experiment_data_by_experiment_id(gs_log_dir, session_id, exp_id)
                for exp_id in experiment_ids]
        aggregator = DataAggregator(experiments_df=exps, smoothing=smoothing)
        data = aggregator.group_by_param(metric_tag, group_by_param)
        return data

    # aggregate data from all experiments based on group by param
    data_groups = prepare_data(metric_tag)

    g = dcc.Graph(
        id=metric_tag,
        figure=get_std_figure(metric_tag, data_groups)
    )
    return g


def get_std_figure(title, data_groups):
    def get_band_traces(name, data, color):
        # calculate bounds
        mean_data, ucb_data, lcb_data = get_deviations(data)

        x = np.arange(mean_data.shape[0])
        upper_bound = go.Scatter(
            name=name,
            x=x,
            y=ucb_data,
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            fillcolor=color,
            fill='tonexty',
            legendgroup=name,
            showlegend=False, )

        trace = go.Scatter(
            name=name,
            x=x,
            y=mean_data,
            mode='lines',
            line=dict(color=color),
            fillcolor=color,
            fill='tonexty',
            legendgroup=name)

        lower_bound = go.Scatter(
            name=name,
            x=x,
            y=lcb_data,
            fillcolor=color,
            line=dict(width=0),
            mode='lines',
            legendgroup=name,
            showlegend=False, )

        # Trace order can be important
        # with continuous error bars
        trace_data = [lower_bound, trace, upper_bound]

        return trace_data

    trace_data = list(
        reduce(lambda x, y: x + get_band_traces(y[0][0], y[0][1], y[1]), zip(data_groups.items(), DEFAULT_PLOTLY_COLORS), []))
    fig = go.Figure(data=trace_data, layout={
        'plot_bgcolor': '#ffffff',
        'showlegend': True
    })

    # center the title
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    return fig


def get_deviations(data):
    m, sd = np.mean(data, axis=0), np.std(data, axis=0)
    return m, m - sd, m + sd


@app.callback(
    Output('hidden-div-placeholder-2', "children"),
    [Input("session-id", "children"), Input('smoothing-slider', 'value'), Input("hidden-log-dir", "children")])
def settings_callback(session_id, smoothing, gs_log_dir):
    GraphController.set_smoothing_factor(gs_log_dir, session_id, smoothing)
    return html.Div("")

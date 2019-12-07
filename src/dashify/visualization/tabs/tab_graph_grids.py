import dash_core_components as dcc
import dash_html_components as html
import os
from dashify.visualization.data_import import GridSearchLoader, Experiment
from dashify.visualization.data_model.in_memory import server_storage
from typing import List, Dict
import operator
from functools import reduce
import numpy as np
import plotly.graph_objs as go
from pandas import DataFrame


def render_graphs(session_id: str, log_dir: str):

    # determine the metrics to be displayed in the graph

    graphs = create_graphs(gs_loader, metrics_df)
    graph_groups = create_graph_groups(graphs)
    grids = create_grids(graph_groups)

    interval = dcc.Interval(
        id='graph-interval-component',
        interval=10*1000,  # in milliseconds
        n_intervals=0
    )
    grids.append(interval)
    return grids

def load_data(session_id: str, log_dir: str):
    metrics_df = server_storage.get(session_id, "Metrics")
    gs_loader = GridSearchLoader(log_dir)



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


def is_std_selected(metrics_df, metric_tag):
    if metrics_df[metrics_df["metrics"] == metric_tag]["Std_band"].iloc[0] == "y":
        return True
    else:
        return False


def is_metric_selected(metrics_df, metric_tag):
    if metrics_df[metrics_df["metrics"] == metric_tag]["Selected"].iloc[0] == "y":
        return True
    else:
        return False


def create_graphs(gs_loader: GridSearchLoader, metrics_df: DataFrame) -> List[dcc.Graph]:
    metric_tags = gs_loader.get_experiment(gs_loader.get_experiment_ids()[0]).metrics.keys()

    # filter the metrics based on selection
    metric_tags = [metric_tag for metric_tag in metric_tags if is_metric_selected(metrics_df, metric_tag)]

    return [create_graph_with_std(metric_tag, gs_loader)
            if is_std_selected(metrics_df, metric_tag)
            else create_graph_with_line_plot(metric_tag, gs_loader)
            for metric_tag in metric_tags]


def create_graph_with_line_plot(metric_tag: str, gs_loader: GridSearchLoader) -> dcc.Graph:
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
                'title': metric_tag,
            }
        }
    )
    return g


def create_graph_with_std(metric_tag: str, gs_loader: GridSearchLoader) -> dcc.Graph:

    def prepare_data(metric_tag: str, gs_loader: GridSearchLoader) -> List:
        experiment_ids = gs_loader.get_experiment_ids()
        return [gs_loader.get_experiment(experiment_id).metrics[metric_tag] for experiment_id in experiment_ids]

    # aggregate data from all experiments
    data = np.array(prepare_data(metric_tag, gs_loader))

    # find confidence intervals
    mean, lower_bound, upper_bound = get_deviations(data)

    g = dcc.Graph(
        id=metric_tag,
        figure=get_std_figure(metric_tag, mean, lower_bound, upper_bound)
    )
    return g


def get_std_figure(title, mean_data, lcb_data, ucb_data):
    x = np.arange(mean_data.shape[0])
    upper_bound = go.Scatter(
        name='Upper Bound',
        x=x,
        y=ucb_data,
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0),
        fillcolor='rgba(68, 68, 68, 0.3)',
        fill='tonexty')

    trace = go.Scatter(
        name='Average Value',
        x=x,
        y=mean_data,
        mode='lines',
        line=dict(color='rgb(31, 119, 180)'),
        fillcolor='rgba(68, 68, 68, 0.3)',
        fill='tonexty')

    lower_bound = go.Scatter(
        name='Lower Bound',
        x=x,
        y=lcb_data,
        marker=dict(color="#444"),
        line=dict(width=0),
        mode='lines')

    # Trace order can be important
    # with continuous error bars
    data = [lower_bound, trace, upper_bound]

    fig = go.Figure(data=data, layout={
        'plot_bgcolor': '#ffffff',
        'showlegend': False
    })

    # center the title
    fig.update_layout(
        title={
            'text': title,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    return fig


def get_deviations(data):
    m, sd = np.mean(data, axis=0), np.std(data, axis=0)
    return m, m-sd, m+sd

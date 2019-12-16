import numpy as np
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS
import dash_core_components as dcc
from typing import List, Dict
from functools import reduce


def generate_marks(min, max, step):
    marks = {}
    for i in np.arange(min, max + 1, step):
        if i % max == 0:
            marks[int(i)] = str(round(i, 2))
        else:
            marks[i] = str(round(i, 2))
    return marks


def make_transparent(color, transparency):
    r, g, b = color.split("(")[1].split(")")[0].split(",")
    color = f"rgba({r}, {g}, {b}, {transparency})"
    return color


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
            line=dict(width=0),
            fillcolor=make_transparent(color, transparency=0.5),
            fill='tonexty',
            legendgroup=name,
            showlegend=False)

        trace = go.Scatter(
            name=name,
            x=x,
            y=mean_data,
            mode='lines',
            line=dict(color=color),
            fillcolor=make_transparent(color, transparency=0.5),
            fill='tonexty',
            legendgroup=name)

        lower_bound = go.Scatter(
            name=name,
            x=x,
            y=lcb_data,
            line=dict(width=0),
            mode='lines',
            legendgroup=name,
            showlegend=False)

        # Trace order can be important
        # with continuous error bars
        trace_data = [lower_bound,
                      trace,
                      upper_bound]

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


def get_deviations(series: List):
    max_len = reduce(lambda x, y: max(x, len(y)), series, 0)
    n_series = len(series)

    mean_series = np.zeros(max_len)
    std_series = np.zeros(max_len)
    for seq_ix in range(max_len):
        series_at_ix = []
        for series_ix in range(n_series):
            try:
                data_point = series[series_ix].pop(seq_ix)
                series_at_ix.append(data_point)
            except:
                pass

        # compute mean and std
        mean, sd = np.mean(series_at_ix), np.std(series_at_ix)
        mean_series[seq_ix] = mean
        std_series[seq_ix] = sd

    return mean_series, mean_series-std_series, mean_series + std_series


def get_line_graph(id, series: List[Dict], title) -> dcc.Graph:
    def create_one_series(name, data) -> Dict:
        series = {"x": list(range(len(data))), 'y': data, 'type': 'linear', 'name': name}
        return series

    def get_series_data(series) -> List:
        return [create_one_series(exp["experiment_id"], exp["data"]) for exp in series]

    graph = dcc.Graph(
        id=id,
        figure={
            'data': get_series_data(series),
            'layout': {
                'title': title,
            }
        }
    )
    return graph


def get_band_graph(id, series_groups: Dict, title) -> dcc.Graph:
    band_graph = dcc.Graph(
        id=id,
        figure=get_std_figure(title, series_groups)
    )
    return band_graph
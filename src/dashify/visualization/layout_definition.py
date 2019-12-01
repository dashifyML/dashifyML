import dash
import dash_core_components as dcc
import dash_html_components as html
from dashify.visualization import Settings

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

app.layout = html.Div(children=[
    html.H1(children='Dashify'),

    html.Div(children=f"analyzing {Settings.log_dir}", id="log-dir"),

    dcc.Tabs(id="tabs", value='tabs', children=[
        dcc.Tab(label='Settings', value='tab-settings'),
        dcc.Tab(label='Table', value='tab-table'),
        dcc.Tab(label='Graphs', value='tab-graphs'),
    ]),
    html.Div(id='tabs-content'),
])


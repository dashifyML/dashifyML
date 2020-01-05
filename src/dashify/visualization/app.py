import dash
from dashify.visualization.controllers.data_controllers import ExperimentController, MetricsController, ConfigController, GridSearchController
from dashify.visualization.controllers import data_controllers
from flask import request
from dashify.metrics.processor import MetricDataProcessor
import flask
from flask import jsonify
import uuid
from dashify.visualization.data_export.analysis_file import AnalysisExporter

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True
app.server.secret_key = str(uuid.uuid4())


@app.server.route('/download_experiments_data')
def download_experiments_data():

    # get session id
    session_id = flask.session.get("session_id")

    # get experiments data
    df_experiments = ExperimentController.get_experiments_df(session_id)
    csv_string = df_experiments.to_csv(index=False, encoding='utf-8')

    return csv_string


@app.server.route("/download_graph_data")
def download_graph_data():

    # get session id and metric id
    session_id = flask.session.get("session_id")
    metric_tag = request.args.get("metric_tag")
    to_aggregate = request.args.get("aggregate")

    if to_aggregate == "True":
        json_data = jsonify(MetricDataProcessor.get_aggregated_data(session_id, metric_tag))
    else:
        json_data = jsonify(MetricDataProcessor.get_data(session_id, metric_tag))

    return json_data

@app.server.route("/download_analysis_data")
def download_analysis_data():
    session_id = flask.session.get("session_id")
    grid_search_id = request.args.get("grid_search_id") # TBD: do we need multiple grid searches here?

    # grid search data
    grid_search_data = AnalysisExporter.pack(session_id, grid_search_id)

    # complete analysis data
    analysis = []
    analysis.append(grid_search_data)
    return jsonify(analysis)
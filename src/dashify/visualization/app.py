import dash
import flask
import io
from dashify.visualization.controllers.data_controllers import ExperimentController
from flask import request

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True


@app.server.route('/download_experiments_data')
def download_experiments_data():

    # get session id and filters
    session_id = request.args.get("session_id")
    filters = request.args.get("filters")

    # get experiments data
    ExperimentController.set_experiment_filters(session_id, filters.split(" && "))
    df_experiments = ExperimentController.get_experiments_df(session_id)
    csv_string = df_experiments.to_csv(index=False, encoding='utf-8')

    return csv_string
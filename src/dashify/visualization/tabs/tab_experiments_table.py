from dash.dependencies import Input, Output
import dash_table
from dashify.visualization.app import app
from dashify.visualization.controllers.data_controllers import ExperimentController
import dash
from flask import url_for


def render_table(session_id: str):
    df_experiments = ExperimentController.get_experiments_df(session_id, aggregate=True)
    filters = ExperimentController.get_experiment_filters_string(session_id)
    return dash_table.DataTable(
        id='table-filtering-be',
        columns=[
            {"name": i, "id": i} for i in sorted(df_experiments.columns)
        ],
        filter_action='custom',
        filter_query=' && '.join(filters)
    )


@app.callback(
    Output('table-filtering-be', "data"),
    [Input('table-filtering-be', "filter_query"), Input("session-id", "children")])
def update_table(filters, session_id):
    ExperimentController.set_experiment_filters(session_id, filters.split(" && "))
    df_experiments = ExperimentController.get_experiments_df(session_id)
    return df_experiments.to_dict('records')


@app.callback(
    dash.dependencies.Output('download-exp-link', 'href'),
    [Input('table-filtering-be', "filter_query"), Input("session-id", "children")])
def update_download_link(filters, session_id):
    url = url_for("download_experiments_data") + f"?session_id={session_id}&&filters={filters}"
    return url

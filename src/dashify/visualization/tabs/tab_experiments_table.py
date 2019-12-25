from dash.dependencies import Input, Output
import dash_table
from dashify.visualization.app import app
from dashify.visualization.controllers.data_controllers import ExperimentController
import dash


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
    [Input('table-filtering-be', "filter_query"), Input("session-id", "children"), Input("download-df", "n_clicks")])
def update_table(filters, session_id, button_clicks):
    ExperimentController.set_experiment_filters(session_id, filters.split(" && "))
    df_experiments = ExperimentController.get_experiments_df(session_id)

    # for download of experiments data
    context = dash.callback_context
    triggered_input = context.triggered[0]["prop_id"].split(".")[0] if context.triggered[0]["value"] is not None else None
    if triggered_input == "download-df":
        print("Download routine ...")

    return df_experiments.to_dict('records')

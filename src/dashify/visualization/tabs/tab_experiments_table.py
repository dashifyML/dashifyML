from dash.dependencies import Input, Output
import dash_table
from dashify.visualization.app import app
from dashify.visualization.data_controllers import ExperimentController


def render_table(log_dir: str, session_id: str):
    df_experiments = ExperimentController.get_experiments_df(log_dir, session_id)
    filters = ExperimentController.get_experiment_filters_string(log_dir, session_id)
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
    [Input('table-filtering-be', "filter_query"), Input("hidden-log-dir", "children"), Input("session-id", "children")])
def update_table(filters, log_dir, session_id):
    ExperimentController.set_experiment_filters(log_dir, session_id, filters.split(" && "))
    df_experiments = ExperimentController.get_experiments_df(log_dir, session_id)
    return df_experiments.to_dict('records')

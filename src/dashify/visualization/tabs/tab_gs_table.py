from dash.dependencies import Input, Output
import dash_table
from dashify.visualization.app import app
import pandas as pd
from typing import List
import dashify.visualization.controller_tab_gs_table as controller_tab_gs_table

def render_table(session_id: str):
    df_gs_table = controller_tab_gs_table.get_gs_table(session_id)
    filters = controller_tab_gs_table.get_gs_table_filters(session_id)
    return dash_table.DataTable(
        id='table-filtering-be',
        columns=[
            {"name": i, "id": i} for i in sorted(df_gs_table.columns)
        ],
        filter_action='custom',
        filter_query=filters
    )

#
#
# @app.callback(
#     Output('table-filtering-be', "data"),
#     [Input('table-filtering-be', "filter_query"), Input("hidden-log-dir", "children"), Input("session-id", "children")])
# def update_table(filter, log_dir, session_id):
#     cache_controller.
#
#     # store filtered grid search table and filters
#     server_storage.insert(session_id, "grid_search_table", df_gs_table)
#     server_storage.insert(session_id, "grid_search_table_filters", filter)
#
#     return df_gs_table.to_dict('records')

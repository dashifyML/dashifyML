import argparse
from dashify.visualization.app import app
from dashify.visualization.layout_definition import get_layout
from dashify.visualization.data_export.analysis_file import AnalysisExporter
import uuid

def parse_args():
    parser = argparse.ArgumentParser(description='Visualize grid search experiments')
    parser.add_argument('--logdir', type=str, help='Path tho the grid search root directory')
    parser.add_argument('--analysis_file', type=str, help='Path to the dashify analysis file (analysis.json)')
    parser.add_argument('--port', type=int, help='Port on which runs the webserver', default=8888)
    args = parser.parse_args()
    gs_log_dir = args.logdir
    port = args.port
    analysis_file = args.analysis_file
    if not gs_log_dir and not analysis_file:
        raise Exception("Please specify either the log dir with --logdir <your grid search log dir> or path to the analysis file (analysis.json)")
    
    return gs_log_dir, analysis_file, port


def run_server(gs_log_dir: str, analysis_file: str, port: int):

    # session id
    session_id = str(uuid.uuid4())

    # here, we unpack the analysis file 
    if analysis_file:
        gs_log_dir = AnalysisExporter.unpack(analysis_file, session_id)
    app.layout = get_layout(gs_log_dir, session_id)
    app.run_server(debug=True, port=port)


if __name__ == '__main__':
    gs_log_dir, analysis_file, port = parse_args()
    run_server(gs_log_dir, analysis_file, port)

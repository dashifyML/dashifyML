import argparse
from dashify.visualization.app import app
from dashify.visualization.layout_definition import get_layout


def parse_args():
    parser = argparse.ArgumentParser(description='Visualize grid search experiments')
    parser.add_argument('--logdir', type=str, help='Path tho the grid search root directory')
    args = parser.parse_args()
    gs_log_dir = args.logdir
    if gs_log_dir is None:
        raise Exception("Please specify the log dir with --logdir <your grid search log dir>")
    else:
        return gs_log_dir


def run_server(gs_log_dir):
    app.layout = get_layout(gs_log_dir)
    app.run_server(debug=True)


if __name__ == '__main__':
    gs_log_dir = parse_args()
    run_server(gs_log_dir)

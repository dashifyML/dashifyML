from dashify.visualization.data_model.grid_search_result import GridSearchResult 
from typing import List, Dict
from dashify.visualization.controllers import data_controllers
from pathlib import Path
import os
import json
from datetime import datetime
from dashify.visualization.controllers import data_controllers
import pandas as pd

class AnalysisExporter:
    @staticmethod
    def pack(session_id: str, grid_search_ids: List[str]) -> List[Dict]:
        """
        Gets the grid search result and packs the obtained grid search result 
        into a list of dict for analysis export
        """

        analysis_data = []
        for grid_search_id in grid_search_ids:

            # grid search result
            grid_search_result = data_controllers.cache_controller.get_gs_results(grid_search_id, session_id)

            # list of experiments
            experiments_data = []
            for experiment in grid_search_result.experiments:
                experiment_dict = {
                    "experiment_id": experiment.identifier,
                    "config": experiment.config,
                    "metrics": experiment.metrics
                }
                experiments_data.append(experiment_dict)
            
            # grid search data with experiments data
            grid_search_dict = {}
            grid_search_dict["grid_search_id"] = grid_search_id
            grid_search_dict["experiments_data"] = experiments_data

            # now, gets the analysis settings
            grid_search_dict["config_settings"] = data_controllers.cache_controller.get_selected_configs_settings(grid_search_id, session_id)
            grid_search_dict["metric_settings"] = data_controllers.cache_controller.get_metrics_settings(grid_search_id, session_id).to_dict()
            grid_search_dict["graph_settings"] = data_controllers.cache_controller.get_graph_smoothing_factor(grid_search_id, session_id)
            grid_search_dict["filter_settings"] = data_controllers.cache_controller.get_experiment_filters(grid_search_id, session_id)

            analysis_data.append(grid_search_dict)
        return analysis_data

    @staticmethod
    def unpack(file_path: str, session_id: str) -> str:
        """
        Loads the analysis file and unpacks into a directory for grid search
        """

        # load the analysis file
        analysis = json.load(open(file_path))

        # create a directory in the home directory (TBD: use export settings)
        import_dir = os.path.join(Path.home(), "dashify_imports", str(datetime.now()))

        # set the log dir
        data_controllers.GridSearchController.set_log_dir(import_dir)

        # unpack
        for grid_search_data in analysis:
            grid_search_id = grid_search_data["grid_search_id"]
            for experiment_data in grid_search_data["experiments_data"]:
                # experiment id, config, metrics
                experiment_id = experiment_data["experiment_id"]
                config = experiment_data["config"]
                metrics = experiment_data["metrics"]

                # create a folder for each experiment
                experiment_folder = os.path.join(import_dir, grid_search_id, experiment_id)
                os.makedirs(experiment_folder)
                json.dump(config, open(os.path.join(experiment_folder, "config.json"), "w"))
                json.dump(metrics, open(os.path.join(experiment_folder, "metrics.json"), "w"))
            
            # Calls bunch of controllers (may not be the elegant way)
            data_controllers.cache_controller.set_selected_configs_settings(grid_search_id, session_id, grid_search_data["config_settings"])
            data_controllers.cache_controller.set_metrics_settings(grid_search_id, session_id, pd.DataFrame.from_dict(grid_search_data["metric_settings"]))
            data_controllers.cache_controller.set_graph_smoothing_factor(grid_search_id, session_id, grid_search_data["graph_settings"])
            data_controllers.cache_controller.set_experiment_filters(grid_search_id, session_id, grid_search_data["filter_settings"])

        return import_dir
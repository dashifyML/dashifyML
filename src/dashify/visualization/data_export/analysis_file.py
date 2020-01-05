from dashify.visualization.data_model.grid_search_result import GridSearchResult 
from typing import List, Dict
from dashify.visualization.controllers import data_controllers
from pathlib import Path
import os
import json
from datetime import datetime

class AnalysisExporter:
    @staticmethod
    def pack(session_id: str, grid_search_id) -> List[Dict]:
        """
        Gets the grid search result and packs the obtained grid search result into a list of dict for analysis export
        """

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
        
        # grid search data
        grid_search_data = {}
        grid_search_data[grid_search_id] = experiments_data

        return grid_search_data

    @staticmethod
    def unpack(file_path: str) -> str:
        """
        Loads the analysis file and unpacks into a directory for grid search
        """

        # load the analysis file
        analysis = json.load(open(file_path))

        # create a directory in the home directory (TBD: use export settings)
        import_dir = os.path.join(Path.home(), "dashify_imports", str(datetime.now()))

        # unpack
        for grid_search_data in analysis:
            for grid_search_id, experiments in grid_search_data.items():
                for experiment_data in experiments:
                    # experiment id, config, metrics
                    experiment_id = experiment_data["experiment_id"]
                    config = experiment_data["config"]
                    metrics = experiment_data["metrics"]

                    # create a folder for each experiment
                    experiment_folder = os.path.join(import_dir, grid_search_id, experiment_id)
                    os.makedirs(experiment_folder)
                    json.dump(config, open(os.path.join(experiment_folder, "config.json"), "w"))
                    json.dump(metrics, open(os.path.join(experiment_folder, "metrics.json"), "w"))
                
        # TBD: Calls bunch of controllers (may not be the elegant way)

        return import_dir
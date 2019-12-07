from dashify.visualization.data_model.experiment import Experiment
from typing import List


class GridSearchResult:
    def __init__(self, log_dir: str, experiments: List[Experiment] = None):
        """
        Dataclass for storing all the experiments of a grid search.
        :param log_dir: Experiments' logging directory of the grid search
        :param experiments: List of experiments
        """
        self.log_dir = log_dir
        if experiments is None:
            experiments = []
        self.experiments = experiments

    def add_experiment(self, experiment: Experiment):
        """
        Adds an experiment to the grid search
        :param experiment: Experiment object
        :return: None
        """
        self.experiments.append(experiment)

    def get_experiment_ids(self) -> List[str]:
        """
        Returns all expriment ids of the grid search
        :return: List[experiment_id]
        """
        return [experiment.identifier for experiment in self.experiments]





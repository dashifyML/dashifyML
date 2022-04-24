from multiprocessing import Lock
from typing import Dict, Any, List
import os
import json
import torch
import torch.nn as nn
from torch.optim.optimizer import Optimizer
import sys
from contextlib import redirect_stderr, redirect_stdout
import traceback
from functools import wraps
import dill as dill


class ResourceLocker:
    __instance = None

    @classmethod
    def get_locker(cls):
        if ResourceLocker.__instance is None:
            ResourceLocker()
        return ResourceLocker.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if ResourceLocker.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            ResourceLocker.__instance = self
            self.resource_access = {}
            self.internal_lock = Lock()

    def acquire(self, resource):
        print(f"Acquiring {resource}")
        self.internal_lock.acquire()

        if resource not in self.resource_access:
            self.resource_access[resource] = Lock()
        self.internal_lock.release()
        lock = self.resource_access[resource]
        lock.acquire()

    def release(self, resource):
        self.internal_lock.acquire()

        if resource not in self.resource_access:
            self.resource_access[resource] = Lock()
        self.internal_lock.release()
        lock = self.resource_access[resource]
        lock.release()


class ExperimentInfo:
    """Data class that collects all information of an experiment
    """

    def __init__(self, log_dir: str, subfolder_id: str, model_name: str, dataset_name: str, run_id: str):
        """

        :param log_dir: directory where all grid search runs are stored
        :param subfolder_id: time stamp
        :param model_name: name of the model
        :param dataset_name: name of the dataset
        :param run_id: id of the grid search run
        :param measurement_id: id of the measurement. For NNs this is generally the epoch number.
        """
        self._log_dir = log_dir
        self._subfolder_id = subfolder_id
        self._model_name = model_name
        self._dataset_name = dataset_name
        self._run_id = run_id

    @property
    def log_dir(self) -> str:
        return self._log_dir

    @property
    def subfolder_id(self) -> str:
        return self._subfolder_id

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dataset_name(self) -> str:
        return self._dataset_name

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def full_experiment_path(self) -> str:
        return os.path.join(self._log_dir, self._subfolder_id, self._model_name, self._dataset_name, self._run_id)

    @property
    def experiment_id(self) -> str:
        return os.path.join(self._subfolder_id, self._model_name, self._dataset_name, self._run_id)

    def create_folder_structure(self):
        full_path = self.full_experiment_path
        if not os.path.exists(full_path):
            os.makedirs(full_path)

    def folder_structure_exists(self) -> bool:
        full_path = self.full_experiment_path
        return os.path.exists(full_path)


class DashifyLogger:
    config_name = "config.json"
    metrics_name = "metrics.json"
    checkpoint_folder = "checkpoints"
    std_out_name = "stdout.txt"
    err_out_name = "errout.txt"

    @classmethod
    def get_experiment_info(cls, log_dir: str, subfolder_id: str, model_name: str, dataset_name: str, run_id: str) -> ExperimentInfo:
        experiment_info = ExperimentInfo(log_dir, subfolder_id, model_name, dataset_name, run_id)
        return experiment_info

    @classmethod
    def save_experiment_info(cls, experiment_info: ExperimentInfo):
        experiment_info.create_folder_structure()
        cls._create_experiment_file(experiment_info, cls.config_name)
        cls._create_experiment_file(experiment_info, cls.metrics_name)
        # std_out_path = os.path.join(experiment_info.full_experiment_path, cls.std_out_name)
        # err_out_path = os.path.join(experiment_info.full_experiment_path, cls.err_out_name)
        # sys.stdout = open(std_out_path, 'w')
        # sys.stdout = open(err_out_path, 'w')

    @classmethod
    def load_existing_experiment(cls, log_dir: str, subfolder_id: str, model_name: str, dataset_name: str,
                                 run_id: str) -> ExperimentInfo:
        experiment_info = ExperimentInfo(log_dir, subfolder_id, model_name, dataset_name, run_id)
        config_path = os.path.join(experiment_info.full_experiment_path, cls.config_name)
        metrics_path = os.path.join(experiment_info.full_experiment_path, cls.metrics_name)
        if not all([os.path.exists(config_path), os.path.exists(metrics_path)]):
            raise Exception(f"Experiment is not present in {experiment_info.full_experiment_path}")
        return experiment_info

    @classmethod
    def save_config(cls, config: Dict, experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        config_path = os.path.join(experiment_folder, cls.config_name)
        with open(config_path, "w") as f:
            json.dump(config, f)

    @classmethod
    def save_dict(cls, file_name: str, config: Dict[str, Any], experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        dict_path = os.path.join(experiment_folder, cls.checkpoint_folder, file_name)
        with open(dict_path, "w") as f:
            json.dump(config, f)

    @classmethod
    def log_raw_experiment_message(cls, file_name: str, config: Dict[str, Any], experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        dict_path = os.path.join(experiment_folder, file_name)
        with open(dict_path, "a") as f:
            json.dump(config, f)

    @classmethod
    def log_raw_gs_message(cls, file_name: str, config: Dict[str, Any], experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        dict_path = os.path.join(experiment_folder, file_name)
        with open(dict_path, "a") as f:
            json.dump(config, f)

    @classmethod
    def load_dict(cls, file_name: str, experiment_info: ExperimentInfo) -> Dict[str, Any]:
        experiment_folder = experiment_info.full_experiment_path
        dict_path = os.path.join(experiment_folder, cls.checkpoint_folder, file_name)
        with open(dict_path, "r") as f:
            d = json.load(f)
        return d

    @classmethod
    def save_checkpoint_state_dict(cls, state_dict: Dict, name: str, experiment_info: ExperimentInfo, measurement_id: int):
        experiment_folder = experiment_info.full_experiment_path
        state_dict_path = os.path.join(experiment_folder, cls.checkpoint_folder, name + "_" + str(measurement_id) + ".pt")
        os.makedirs(os.path.dirname(state_dict_path), exist_ok=True)  # creates intermediate folders
        torch.save(state_dict, state_dict_path, pickle_module=dill)

    @classmethod
    def load_checkpoint_state_dict(cls, name: str, experiment_info: ExperimentInfo, measurement_id: int) -> Dict:
        experiment_folder = experiment_info.full_experiment_path
        state_dict_path = os.path.join(experiment_folder, cls.checkpoint_folder,
                                       name + "_" + str(measurement_id) + ".pt")
        state_dict = torch.load(state_dict_path)
        return state_dict

    @classmethod
    def log_metrics(cls, metrics: Dict[str, List[float]], experiment_info: ExperimentInfo, measurement_id: int):
        """ Logs a metrics dictionary to disc.

        :param metrics: Dictionary containing the metrics
        :param experiment_info: Contains all necessary information to uniquely identify the experiment
        :param measurement_id: Measurement id of the captures meatrics. Generally, this is the epoch.
        """
        experiment_folder = experiment_info.full_experiment_path
        metrics_path = os.path.join(experiment_folder, cls.metrics_name)
        with open(metrics_path, "r") as f:
            stored_metrics = json.load(f)
        merged_dict = DashifyLogger._merge_dictionaries(stored_metrics, metrics, measurement_id)
        with open(metrics_path, "w") as f:
            json.dump(merged_dict, f)

    # helper methods

    @classmethod
    def _create_experiment_file(cls, experiment_info: ExperimentInfo, file_name: str):
        full_path = os.path.join(experiment_info.full_experiment_path, file_name)
        with open(full_path, "w") as f:
            json.dump({}, f)

    @staticmethod
    def _merge_dictionaries(dict_1: Dict[str, List[Any]], dict_2: Dict[str, List[Any]], measurement_id: int) -> \
            Dict[str, List[Any]]:
        """ Merges two dictionaries mapping str to List.

        :param dict_1:
        :param dict_2:
        :param measurement_id: For each key, the values from `measurement_id` to `len(dict_2[key])` are replaced (in place).
        :return: merged dictionaries
        """
        merged = dict_1.copy()
        for key, value in dict_2.items():
            if key not in merged:
                merged[key] = dict_2[key]
            else:
                merged[key] = merged[key][:measurement_id] + dict_2[key] + merged[key][measurement_id + len(dict_2[key]) - 1:]
        return merged


class ExperimentTracking(object):
    def __init__(self, experiment_info: ExperimentInfo, log_to_file: bool = False):
        self.log_to_file = log_to_file
        self.experiment_info = experiment_info

    def __call__(self, run_fun):
        @wraps(run_fun)
        def decorate_run(**fun_params: Dict[str, Any]):
            if self.log_to_file:
                self.redirect_function_output(run_fun, fun_params, self.experiment_info)
            else:
                self.run_fun_with_reraise(run_fun, fun_params, file=None)

        return decorate_run

    def redirect_function_output(self, run_fun, fun_params: Dict[str, Any], experiment_info: ExperimentInfo):
        stdout_file = os.path.join(experiment_info.full_experiment_path, DashifyLogger.std_out_name)
        stderr_file = os.path.join(experiment_info.full_experiment_path, DashifyLogger.err_out_name)

        with open(stdout_file, 'w') as f_stdout:
            with open(stderr_file, 'w') as f_stderr:
                with redirect_stdout(f_stdout):
                    with redirect_stderr(f_stderr):
                        self.run_fun_with_reraise(run_fun=run_fun, file=sys.stderr, fun_params=fun_params)

    def run_fun_with_reraise(self, run_fun, fun_params: Dict[str, Any], file=None):
        try:
            run_fun(**fun_params)  # here we call the scripts run method
        except Exception as e:
            print(e)
            traceback.print_tb(e.__traceback__, file=file)
            raise e

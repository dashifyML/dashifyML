from multiprocessing import Lock
from typing import Dict
import os
import json
import torch
import torch.nn as nn
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
    def __init__(self, log_dir: str, subfolder_id: str, model_name: str, dataset_name: str, run_id: str):
        self._log_dir = log_dir  # directory where all grid search runs are stored
        self._subfolder_id = subfolder_id  # time stamp
        self._model_name = model_name  # name of the model
        self._dataset_name = dataset_name  # name of the dataset
        self._run_id = run_id  # id of the grid search run

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


class DashifyLogger:
    config_name = "config.json"
    metrics_name = "metrics.json"
    model_name = "model.pickle"
    std_out_name = "stdout.txt"
    err_out_name = "errout.txt"

    @classmethod
    def create_new_experiment(cls, log_dir: str, subfolder_id: str, model_name: str, dataset_name: str,
                              run_id: str) -> ExperimentInfo:
        experiment_info = ExperimentInfo(log_dir, subfolder_id, model_name, dataset_name, run_id)
        experiment_info.create_folder_structure()
        cls._create_experiment_file(experiment_info, cls.config_name)
        cls._create_experiment_file(experiment_info, cls.metrics_name)
        std_out_path = os.path.join(experiment_info.full_experiment_path, cls.std_out_name)
        err_out_path = os.path.join(experiment_info.full_experiment_path, cls.err_out_name)
        sys.stdout = open(std_out_path, 'w')
        sys.stdout = open(err_out_path, 'w')
        return experiment_info

    @classmethod
    def save_config(cls, config: Dict, experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        config_path = os.path.join(experiment_folder, cls.config_name)
        with open(config_path, "w") as f:
            json.dump(config, f)

    @classmethod
    def save_model(cls, model: nn.Module, experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        model_path = os.path.join(experiment_folder, cls.model_name)
        torch.save(model, model_path, pickle_module=dill)

    @classmethod
    def load_model(cls, experiment_info: ExperimentInfo) -> nn.Module:
        experiment_folder = experiment_info.full_experiment_path
        model_path = os.path.join(experiment_folder, cls.model_name)
        model = torch.load(model_path)
        return model

    @classmethod
    def log_metrics(cls, metrics: Dict, experiment_info: ExperimentInfo):
        experiment_folder = experiment_info.full_experiment_path
        metrics_path = os.path.join(experiment_folder, cls.metrics_name)
        with open(metrics_path, "r") as f:
            stored_metrics = json.load(f)
        merged_dict = DashifyLogger._merge_dictionaries(stored_metrics, metrics)
        with open(metrics_path, "w") as f:
            json.dump(merged_dict, f)

    # helper methods

    @classmethod
    def _create_experiment_file(cls, experiment_info: ExperimentInfo, file_name: str):
        full_path = os.path.join(experiment_info.full_experiment_path, file_name)
        with open(full_path, "w") as f:
            json.dump({}, f)

    @staticmethod
    def _merge_dictionaries(dict_1: Dict, dict_2: Dict) -> Dict:
        merged = dict_1.copy()
        for key, value in dict_2.items():
            if key not in merged:
                merged[key] = [dict_2[key]]
            else:
                merged[key] = merged[key] + [dict_2[key]]
        return merged


class ExperimentTracking(object):
    def __init__(self, log_to_file: bool = False):
        self.log_to_file = log_to_file

    def __call__(self, run_fun):
        @wraps(run_fun)
        def decorate_run(config: Dict, device: torch.device, experiment_info: ExperimentInfo = None):
            DashifyLogger.save_config(config=config, experiment_info=experiment_info)

            if self.log_to_file:
                self.redirect_function_output(run_fun, config, device, experiment_info)
            else:
                self.run_fun_with_reraise(run_fun, config, device, experiment_info, file=None)

        return decorate_run

    def redirect_function_output(self, run_fun, config: dict, device: torch.device, experiment_info: ExperimentInfo):
        stdout_file = os.path.join(experiment_info.full_experiment_path, DashifyLogger.std_out_name)
        stderr_file = os.path.join(experiment_info.full_experiment_path, DashifyLogger.err_out_name)

        with open(stdout_file, 'w') as f_stdout:
            with open(stderr_file, 'w') as f_stderr:
                with redirect_stdout(f_stdout):
                    with redirect_stderr(f_stderr):
                        self.run_fun_with_reraise(run_fun, config, device, experiment_info, file=sys.stderr)

    def run_fun_with_reraise(self, run_fun, config: dict, device: torch.device, experiment_info: ExperimentInfo, file=None):
        try:
            run_fun(config, device, experiment_info)  # here we call the scripts run method
        except Exception as e:
            print(e)
            # traceback.print_exc(file=file)
            traceback.print_tb(e.__traceback__, file=file)
            raise e

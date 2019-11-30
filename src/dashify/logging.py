from multiprocessing import Lock
from typing import Dict
import os
from dashify import log_dir_path
import json
import torch
import torch.nn as nn
import sys
from contextlib import redirect_stderr, redirect_stdout
import traceback
from functools import wraps


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


class DashifyLogger:
    config_name = "config.json"
    metrics_name = "metrics.json"
    model_name = "model.pickle"
    std_out_name = "stdout.txt"
    err_out_name = "errout.txt"

    @classmethod
    def create_new_experiment(cls, run_id, subfolder_id, model_name: str, dataset_name: str) -> str:
        experiment_id = cls._create_experiment_path(run_id, subfolder_id, model_name, dataset_name)
        cls._create_experiment_file(experiment_id, cls.config_name)
        cls._create_experiment_file(experiment_id, cls.metrics_name)
        std_out_path = os.path.join(log_dir_path, experiment_id, cls.std_out_name)
        err_out_path = os.path.join(log_dir_path, experiment_id, cls.err_out_name)
        sys.stdout = open(std_out_path, 'w')
        sys.stdout = open(err_out_path, 'w')
        print("test")
        return experiment_id

    @classmethod
    def save_config(cls, config: Dict, experiment_id: str):
        experiment_folder = cls._get_experiment_folder_from_experiment_id(experiment_id)
        config_path = os.path.join(experiment_folder, cls.config_name)
        with open(config_path, "w") as f:
            json.dump(config, f)

    @classmethod
    def save_model(cls, model: nn.Module, experiment_id: str):
        experiment_folder = cls._get_experiment_folder_from_experiment_id(experiment_id)
        model_path = os.path.join(experiment_folder, cls.model_name)
        model.clean_up()
        torch.save(model, model_path)

    @classmethod
    def load_model(cls, experiment_id: str) -> nn.Module:
        experiment_folder = cls._get_experiment_folder_from_experiment_id(experiment_id)
        model_path = os.path.join(experiment_folder, cls.model_name)
        model = torch.load(model_path)
        return model

    @classmethod
    def log_metrics(cls, metrics: Dict, experiment_id: str):
        experiment_folder = cls._get_experiment_folder_from_experiment_id(experiment_id)
        metrics_path = os.path.join(experiment_folder, cls.metrics_name)
        with open(metrics_path, "r") as f:
            stored_metrics = json.load(f)
        merged_dict = DashifyLogger._merge_dictionaries(stored_metrics, metrics)
        with open(metrics_path, "w") as f:
            json.dump(merged_dict, f)

    # helper methods
    @classmethod
    def _create_experiment_path(cls, run_id, subfolder_id, model_name: str, dataset_name: str) -> str:
        full_path = os.path.join(log_dir_path, subfolder_id, model_name, dataset_name, run_id)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        rel_path = os.path.join(subfolder_id, model_name, dataset_name, run_id)
        return rel_path

    @classmethod
    def _create_experiment_file(cls, experiment_id: str, file_name: str):
        full_path = os.path.join(cls._get_experiment_folder_from_experiment_id(experiment_id), file_name)
        with open(full_path, "w") as f:
            json.dump({}, f)

    @classmethod
    def _get_experiment_folder_from_experiment_id(cls, experiment_id: str) -> str:
        experiment_dir = os.path.join(log_dir_path, experiment_id)
        return experiment_dir

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
    # def __init__(self):
    #     pass

    def __call__(self, run_fun):
        @wraps(run_fun)
        def decorate_run(run_id: str, config: Dict, device, subfolder_id: str):
            experiment_id = DashifyLogger.create_new_experiment(run_id=run_id,
                                                                subfolder_id=subfolder_id,
                                                                model_name=config["model"]["type"],
                                                                dataset_name=config["dataset"])
            DashifyLogger.save_config(config=config, experiment_id=experiment_id)

            stdout_file = os.path.join(log_dir_path, experiment_id, DashifyLogger.std_out_name)
            stderr_file = os.path.join(log_dir_path, experiment_id, DashifyLogger.err_out_name)

            with open(stdout_file, 'w') as f_stdout:
                with open(stderr_file, 'w') as f_stderr:
                    with redirect_stdout(f_stdout):
                        with redirect_stderr(f_stderr):
                            try:
                                run_fun(config, device, experiment_id)  # here we call the scripts run method
                            except Exception as e:
                                traceback.print_tb(e.__traceback__, file=sys.stderr)
            return

        return decorate_run
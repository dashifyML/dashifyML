from dashify.visualization.controllers.data_controllers import ExperimentController, GraphController, MetricsController
from dashify.aggregation.aggregator import DataAggregator
from typing import Dict
from tqdm import tqdm


class MetricDataProcessor:
    """
    To get data for plots or for download
    """

    @staticmethod
    def get_data(session_id: str, metric_tag: str):
        """
        Gets data (un aggregated) for all experiments
        """
        smoothing = GraphController.get_smoothing_factor(session_id)
        experiment_ids = ExperimentController.get_experiment_ids(session_id)
        metric_data = ExperimentController.get_experiment_data_by_experiment_id(session_id, experiment_ids, [metric_tag])

        def prepare_single_data_series(experiment_id: str) -> Dict:
            data = metric_data[metric_data["experiment_id"] == experiment_id][metric_tag].values[0]
            data = data if isinstance(data, list) else []
            data = DataAggregator.smooth(data, smoothing)
            dict_data = {
                "experiment_id": experiment_id,
                "data": data
            }
            return dict_data

        series = []
        for experiment_id in tqdm(experiment_ids):
            series.append(prepare_single_data_series(experiment_id))

        return series

    @staticmethod
    def get_aggregated_data(session_id: str, metric_tag: str):
        """
        Gets aggregated data for all experiments
        """
        smoothing = GraphController.get_smoothing_factor(session_id)
        group_by_param = MetricsController.get_metric_setting_by_metric_tag(session_id, metric_tag, "Grouping parameter")
        experiment_ids = ExperimentController.get_experiment_ids(session_id)
        metric_data_df = ExperimentController.get_experiment_data_by_experiment_id(session_id, experiment_ids)

        def prepare_data(metric_tag: str) -> Dict:
            aggregator = DataAggregator(experiments_df=metric_data_df, smoothing=smoothing)
            data = aggregator.group_by_param(metric_tag, group_by_param)
            return data

        # aggregate data and get band graph
        data_groups = prepare_data(metric_tag)

        return data_groups

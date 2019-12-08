from typing import Dict


class Experiment:
    def __init__(self, config=None, metrics: Dict[str, float]=None, identifier: str=None):
        self._config = config
        self._metrics = metrics
        self._identifier = identifier

    @property
    def config(self) -> Dict:
        return self._config

    @config.setter
    def config(self, value: Dict):
        self._config = value

    @property
    def metrics(self) -> Dict[str, float]:
        return self._metrics

    @metrics.setter
    def metrics(self, value: Dict[str, float]):
        self._metrics = value

    @property
    def identifier(self) -> str:
        return self._identifier

    @identifier.setter
    def identifier(self, value: str):
        self._identifier = value

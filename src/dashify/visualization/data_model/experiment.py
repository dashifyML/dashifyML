from typing import Dict


class Experiment:
    def __init__(self, config:Dict, metrics: Dict[str, float], identifier: str):
        self._config = config
        self._metrics = metrics
        self._identifier = identifier

    @property
    def config(self) -> Dict:
        return self._config.copy()

    @property
    def metrics(self) -> Dict[str, float]:
        return self._metrics.copy()

    @property
    def identifier(self) -> str:
        return self._identifier

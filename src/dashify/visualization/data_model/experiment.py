class Experiment:
    def __init__(self, config=None, metrics=None, identifier=None):
        self._config = config
        self._metrics = metrics
        self._identifier = identifier

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    @property
    def metrics(self):
        return self._metrics

    @metrics.setter
    def metrics(self, value):
        self._metrics = value

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, value):
        self._identifier = value

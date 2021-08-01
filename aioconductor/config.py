import typing as t
from abc import ABC, abstractmethod

from .component import Component


Config = t.Mapping[str, t.Any]


class ConfigPolicy(ABC):
    @abstractmethod
    def __call__(self, component_class: t.Type[Component]) -> Config:
        """Returns config for a component"""


class SimpleConfigPolicy(ConfigPolicy):

    _config: Config

    def __init__(self, config: Config) -> None:
        self._config = config

    def __call__(self, component_class: t.Type[Component]) -> Config:
        return self._config

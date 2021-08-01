import typing as t
from abc import ABC, abstractmethod
from logging import Logger, getLogger as get_logger

from .component import Component
from .naming import camelcase_to_underscore


class LoggingPolicy(ABC):
    @abstractmethod
    def __call__(self, component_class: t.Type[Component]) -> Logger:
        """Returns logger for a component"""


class SimpleLoggingPolicy(LoggingPolicy):
    def __init__(self, logger: Logger):
        self._logger = logger

    def __call__(self, component_class: t.Type[Component]) -> Logger:
        return self._logger


class ModuleLoggingPolicy(LoggingPolicy):
    def __call__(self, component_class: t.Type[Component]) -> Logger:
        return get_logger(component_class.__module__)


class ComponentLoggingPolicy(LoggingPolicy):
    def __call__(self, component_class: t.Type[Component]) -> Logger:
        return get_logger(
            f"{component_class.__module__}."
            f"{camelcase_to_underscore(component_class.__name__)}"
        )

import asyncio
import signal
import typing as t
from warnings import warn

from .component import Component
from .config import Config, ConfigPolicy, SimpleConfigPolicy
from .logging import (
    Logger,
    LoggingPolicy,
    SimpleLoggingPolicy,
    ModuleLoggingPolicy,
    get_logger,
)
from .exc import CircularDependencyError


T = t.TypeVar("T", bound=Component)


class Conductor:
    config_policy: ConfigPolicy
    logging_policy: LoggingPolicy
    logger: Logger
    loop: asyncio.AbstractEventLoop

    patches: t.Dict[t.Type[Component], t.Type[Component]]
    components: t.Dict[t.Type[Component], Component]

    def __init__(
        self,
        config_policy: t.Optional[ConfigPolicy] = None,
        logging_policy: t.Optional[LoggingPolicy] = None,
        config: t.Optional[Config] = None,
        logger: t.Optional[Logger] = None,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        if config is not None:
            warn(
                "Parameter ``config`` is deprecated, "
                "consider to use ``config_policy`` instead",
                DeprecationWarning,
            )
        if logger is not None:
            warn(
                "Parameter ``logger`` is deprecated, "
                "consider to use ``logging_policy`` instead",
                DeprecationWarning,
            )
        if config_policy is None:
            config_policy = SimpleConfigPolicy(config if config is not None else {})
        if logging_policy is None:
            if logger is not None:
                logging_policy = SimpleLoggingPolicy(logger)
            else:
                logging_policy = ModuleLoggingPolicy()
        self.config_policy = config_policy
        self.logging_policy = logging_policy
        self.logger = logger or get_logger("aioconductor")
        self.loop = loop or asyncio.get_event_loop()
        self.patches = {}
        self.components = {}

    def patch(
        self,
        component_class: t.Type[Component],
        patch_class: t.Type[Component],
    ) -> None:
        self.patches[component_class] = patch_class

    def add(self, component_class: t.Type[T]) -> T:
        actual_class = self.patches.get(component_class, component_class)
        try:
            component = self.components[actual_class]
        except KeyError:
            self.components[actual_class] = component = actual_class(
                config=self.config_policy(actual_class),
                logger=self.logging_policy(actual_class),
                loop=self.loop,
            )
        return t.cast(T, component)

    async def setup(self) -> None:
        scheduled: t.Set[Component] = set()
        aws: t.List[t.Awaitable] = []

        def schedule_setup(component: T, chain: t.Tuple[Component, ...] = ()) -> T:
            if component in scheduled:
                return component
            chain += (component,)
            depends_on = {}
            for name, dependency_class in component.__depends_on__.items():
                dependency = self.add(dependency_class)
                if dependency in chain:
                    raise CircularDependencyError(*chain, dependency)
                depends_on[name] = schedule_setup(dependency, chain)
            aws.append(component._setup(depends_on))
            scheduled.add(component)
            return component

        self.logger.info("Setting up components...")
        for component in tuple(self.components.values()):
            schedule_setup(component)
        await asyncio.gather(*aws)
        self.logger.info("All components are active")

    async def shutdown(self) -> None:
        self.logger.info("Shutting down components...")
        await asyncio.gather(
            *(component._shutdown() for component in self.components.values())
        )
        self.logger.info("All components are inactive")

    def run(self, aw: t.Awaitable) -> None:
        self.loop.run_until_complete(self.setup())
        try:
            self.loop.run_until_complete(aw)
        finally:
            self.loop.run_until_complete(self.shutdown())

    def serve(self) -> None:
        try:
            self.loop.run_until_complete(self.setup())
            self.loop.add_signal_handler(signal.SIGINT, self.loop.stop)
            self.loop.add_signal_handler(signal.SIGTERM, self.loop.stop)
            self.logger.info("Serving...")
            self.loop.run_forever()
        except KeyboardInterrupt:  # pragma: no cover
            pass
        finally:
            self.loop.remove_signal_handler(signal.SIGINT)
            self.loop.remove_signal_handler(signal.SIGTERM)
            self.loop.run_until_complete(self.shutdown())

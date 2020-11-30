import asyncio
import logging
import signal
import typing as t

from .component import Component
from .exc import CircularDependencyError


T = t.TypeVar("T", bound=Component)


class Conductor:
    config: t.Dict[str, t.Any]
    logger: logging.Logger
    loop: asyncio.AbstractEventLoop

    patches: t.Dict[t.Type[Component], t.Type[Component]]
    components: t.Dict[t.Type[Component], Component]

    def __init__(
        self,
        config: t.Dict[str, t.Any],
        logger: logging.Logger = None,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        self.config = config
        self.logger = logger or logging.getLogger("aioconductor")
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
        try:
            component = self.components[component_class]
        except KeyError:
            actual_class = self.patches.get(component_class, component_class)
            self.components[component_class] = component = actual_class(
                self.config,
                self.logger,
                self.loop,
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

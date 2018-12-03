import asyncio
import logging
import signal

from typing import Type, Any, Awaitable, List, Set, Dict

from .component import Component


class Conductor:
    config: Dict[str, Any]
    logger: logging.Logger
    loop: asyncio.AbstractEventLoop

    patches: Dict[Type[Component], Type[Component]]
    components: Dict[Type[Component], Component]

    def __init__(
        self,
        config: Dict[str, Any],
        logger: logging.Logger = None,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        self.config = config
        self.logger = logger or logging.getLogger("aioconductor")
        self.loop = loop or asyncio.get_event_loop()
        self.patches = {}
        self.components = {}

    def patch(
        self, component_class: Type[Component], patch_class: Type[Component]
    ) -> None:
        self.patches[component_class] = patch_class

    def add(self, component_class: Type[Component]) -> Component:
        try:
            return self.components[component_class]
        except KeyError:
            pass
        actual_class = self.patches.get(component_class, component_class)
        self.components[component_class] = component = actual_class(
            self.config, self.logger, self.loop
        )
        return component

    async def setup(self) -> None:
        scheduled: Set[Component] = set()
        aws: List[Awaitable] = []

        def schedule_setup(component):
            if component in scheduled:
                return component
            aws.append(
                component.setup(
                    **{
                        name: schedule_setup(self.add(dependency_class))
                        for name, dependency_class in component.__depends_on__.items()
                    }
                )
            )
            scheduled.add(component)
            return component

        self.logger.info("Setting up components...")
        for component in tuple(self.components.values()):
            schedule_setup(component)
        await asyncio.gather(*aws, loop=self.loop)
        self.logger.info("All components are active")

    async def shutdown(self) -> None:
        self.logger.info("Shutting down components...")
        await asyncio.gather(
            *(component.shutdown() for component in self.components.values()),
            loop=self.loop
        )
        self.logger.info("All components are inactive")

    def run(self, aw: Awaitable) -> None:
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

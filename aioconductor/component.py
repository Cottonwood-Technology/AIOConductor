import asyncio
import logging

from typing import ClassVar, Type, Any, Set, Dict


class Component:
    __depends_on__: ClassVar[Dict[str, Type["Component"]]] = {}

    config: Dict[str, Any]
    logger: logging.Logger
    loop: asyncio.AbstractEventLoop

    active: asyncio.Event
    released: asyncio.Event

    required_by: Set["Component"]
    depends_on: Set["Component"]

    def __init_subclass__(cls) -> None:
        cls.__depends_on__ = {}
        for base in reversed(cls.__mro__):
            if issubclass(base, Component):
                try:
                    annotations = base.__dict__["__annotations__"]
                except KeyError:
                    continue
                cls.__depends_on__.update(
                    (attr, class_)
                    for attr, class_ in annotations.items()
                    if isinstance(class_, type) and issubclass(class_, Component)
                )

    def __init__(
        self,
        config: Dict[str, Any],
        logger: logging.Logger,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.config = config
        self.logger = logger
        self.loop = loop

        self.active = asyncio.Event(loop=loop)
        self.released = asyncio.Event(loop=loop)
        self.released.set()

        self.required_by = set()
        self.depends_on = set()

    def __repr__(self):
        return f"<{self.__class__.__module__}.{self.__class__.__name__}()>"

    async def acquire(self, component: "Component") -> None:
        await self.active.wait()
        self.required_by.add(component)
        self.released.clear()

    async def release(self, component: "Component") -> None:
        self.required_by.remove(component)
        if not self.required_by:
            self.released.set()

    async def setup(self, **depends_on: "Component") -> None:
        if depends_on:
            self.logger.info("%r: Acquiring dependencies...", self)
            aws = []
            for name, component in depends_on.items():
                setattr(self, name, component)
                self.depends_on.add(component)
                aws.append(component.acquire(self))
            await asyncio.gather(*aws, loop=self.loop)
        self.logger.info("%r: Setting up...", self)
        await self.on_setup()
        self.active.set()
        self.logger.info("%r: Active", self)

    async def shutdown(self) -> None:
        if self.required_by:
            self.logger.info("%r: Waiting for release...", self)
            await self.released.wait()
        self.logger.info("%r: Shutting down...", self)
        try:
            await self.on_shutdown()
        except Exception:  # pragma: no cover
            self.logger.exception("%r: Unexpected error during shutdown", self)
        if self.depends_on:
            await asyncio.gather(
                *(component.release(self) for component in self.depends_on),
                loop=self.loop,
            )
            self.depends_on.clear()
        self.active.clear()
        self.logger.info("%r: Inactive", self)

    async def on_setup(self) -> None:
        """ This method should be implemented by child class """

    async def on_shutdown(self) -> None:
        """ This method should be implemented by child class """

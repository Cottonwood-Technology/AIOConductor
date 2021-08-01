import asyncio
import logging
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from .config import Config


class Component:
    __depends_on__: t.ClassVar[t.Dict[str, t.Type["Component"]]] = {}

    config: "Config"
    logger: logging.Logger
    loop: asyncio.AbstractEventLoop

    _active: asyncio.Event
    _released: asyncio.Event

    required_by: t.Set["Component"]
    depends_on: t.Set["Component"]

    def __init_subclass__(cls) -> None:
        cls.__depends_on__ = {}
        for base in reversed(cls.__mro__):
            try:
                annotations = base.__dict__["__annotations__"]
            except KeyError:
                pass
            else:
                cls.__depends_on__.update(
                    (attr, class_)
                    for attr, class_ in annotations.items()
                    if isinstance(class_, type) and issubclass(class_, Component)
                )

    def __init__(
        self,
        config: "Config",
        logger: logging.Logger,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.config = config
        self.logger = logger
        self.loop = loop

        self._active = asyncio.Event()
        self._released = asyncio.Event()
        self._released.set()

        self.required_by = set()
        self.depends_on = set()

    def __repr__(self):
        return f"<{self.__class__.__module__}.{self.__class__.__name__}()>"

    async def _acquire(self, component: "Component") -> None:
        await self._active.wait()
        self.required_by.add(component)
        self._released.clear()

    async def _release(self, component: "Component") -> None:
        self.required_by.remove(component)
        if not self.required_by:
            self._released.set()

    async def _setup(self, depends_on: t.Dict[str, "Component"]) -> None:
        if depends_on:
            self.logger.info("%r: Acquiring dependencies...", self)
            aws = []
            for name, component in depends_on.items():
                setattr(self, name, component)
                self.depends_on.add(component)
                aws.append(component._acquire(self))
            await asyncio.gather(*aws)
        self.logger.info("%r: Setting up...", self)
        await self.on_setup()
        self._active.set()
        self.logger.info("%r: Active", self)

    async def _shutdown(self) -> None:
        if self.required_by:
            self.logger.info("%r: Waiting for release...", self)
            await self._released.wait()
        self.logger.info("%r: Shutting down...", self)
        try:
            await self.on_shutdown()
        except Exception:  # pragma: no cover
            self.logger.exception("%r: Unexpected error during shutdown", self)
        if self.depends_on:
            await asyncio.gather(
                *(component._release(self) for component in self.depends_on)
            )
            self.depends_on.clear()
        self._active.clear()
        self.logger.info("%r: Inactive", self)

    async def on_setup(self) -> None:
        """ This method should be implemented by child class """

    async def on_shutdown(self) -> None:
        """ This method should be implemented by child class """

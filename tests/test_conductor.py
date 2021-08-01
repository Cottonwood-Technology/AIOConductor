import asyncio

import pytest  # type: ignore

from aioconductor import Conductor, Component, CircularDependencyError


@pytest.mark.asyncio
async def test_setup_and_shutdown(event_loop: asyncio.AbstractEventLoop) -> None:
    setup_log = []
    shutdown_log = []

    class A(Component):
        async def on_setup(self) -> None:
            setup_log.append("a")

        async def on_shutdown(self) -> None:
            shutdown_log.append("a")

    class B(Component):
        a: A

        async def on_setup(self) -> None:
            setup_log.append("b")

        async def on_shutdown(self) -> None:
            shutdown_log.append("b")

    class C(Component):
        a: A

        async def on_setup(self) -> None:
            setup_log.append("c")

        async def on_shutdown(self) -> None:
            shutdown_log.append("c")

    class D(Component):
        b: B
        c: C

        async def on_setup(self) -> None:
            setup_log.append("d")

        async def on_shutdown(self) -> None:
            shutdown_log.append("d")

    conductor = Conductor(config={}, loop=event_loop)

    d = conductor.add(D)

    await conductor.setup()
    assert setup_log in (["a", "b", "c", "d"], ["a", "c", "b", "d"])

    a = conductor.add(A)
    b = conductor.add(B)
    c = conductor.add(C)

    assert a.loop is conductor.loop
    assert a.config is conductor.config
    assert a._active.is_set()

    assert b.loop is conductor.loop
    assert b.config is conductor.config
    assert b._active.is_set()
    assert b.a is a

    assert c.loop is conductor.loop
    assert c.config is conductor.config
    assert c._active.is_set()
    assert c.a is a

    assert d.loop is conductor.loop
    assert d.config is conductor.config
    assert d._active.is_set()
    assert d.b is b
    assert d.c is c

    await conductor.shutdown()
    assert shutdown_log in (["d", "b", "c", "a"], ["d", "c", "b", "a"])

    assert not a._active.is_set()
    assert not b._active.is_set()
    assert not c._active.is_set()
    assert not d._active.is_set()


@pytest.mark.asyncio
async def test_circular_dependency_error(event_loop: asyncio.AbstractEventLoop) -> None:
    class A(Component):
        pass

    class B(Component):
        a: A

    class C(Component):
        b: B

    class D(A):
        c: C

    class E(Component):
        c: C

    conductor = Conductor(config={}, loop=event_loop)
    conductor.patch(A, D)
    conductor.add(E)

    with pytest.raises(CircularDependencyError) as info:
        await conductor.setup()
    assert info.value.args == (
        conductor.add(E),
        conductor.add(C),
        conductor.add(B),
        conductor.add(A),
        conductor.add(C),
    )


@pytest.mark.asyncio
async def test_patch(event_loop: asyncio.AbstractEventLoop) -> None:
    class A(Component):
        pass

    class B(Component):
        pass

    class Patch(Component):
        pass

    class C(Component):
        a: A
        b: B

    conductor = Conductor(config={}, loop=event_loop)
    conductor.patch(A, Patch)
    conductor.patch(B, Patch)

    c = conductor.add(C)

    await conductor.setup()

    a = conductor.add(A)
    b = conductor.add(B)

    assert isinstance(a, Patch)
    assert isinstance(b, Patch)
    assert c.a is a
    assert c.b is b
    assert a is b


def test_run(event_loop: asyncio.AbstractEventLoop) -> None:
    setup_log = []
    shutdown_log = []
    run_log = []

    class A(Component):
        async def on_setup(self) -> None:
            setup_log.append("a")

        async def on_shutdown(self) -> None:
            shutdown_log.append("a")

        async def run(self) -> None:
            run_log.append("a")

    conductor = Conductor(config={}, loop=event_loop)
    a = conductor.add(A)
    conductor.run(a.run())

    assert setup_log == ["a"]
    assert run_log == ["a"]
    assert shutdown_log == ["a"]
    assert not a._active.is_set()


def test_serve(event_loop: asyncio.AbstractEventLoop) -> None:
    setup_log = []
    shutdown_log = []
    run_log = []

    class A(Component):

        counter: int

        async def on_setup(self) -> None:
            setup_log.append("a")
            self.counter = 0

        async def on_shutdown(self) -> None:
            shutdown_log.append("a")

        async def request(self) -> int:
            run_log.append("a")
            self.counter += 1
            return self.counter

    class B(Component):

        a: A
        run_task: asyncio.Task

        async def on_setup(self) -> None:
            setup_log.append("b")
            self.run_task = self.loop.create_task(self.run())

        async def on_shutdown(self) -> None:
            self.run_task.cancel()
            shutdown_log.append("b")

        async def run(self) -> None:
            try:
                while await self.a.request() < 3:
                    await asyncio.sleep(0.00001)
                self.loop.stop()
            except asyncio.CancelledError:
                pass

    conductor = Conductor(config={}, loop=event_loop)
    b = conductor.add(B)
    conductor.serve()

    assert setup_log == ["a", "b"]
    assert run_log == ["a", "a", "a"]
    assert shutdown_log == ["b", "a"]
    assert not b._active.is_set()
    assert b.run_task.done()

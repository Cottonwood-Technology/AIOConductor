import asyncio
import logging

import pytest

from aioconductor import Component


def test_depends_on():
    class A(Component):
        pass

    class B(Component):
        pass

    class C(Component):
        pass

    class X(Component):
        component_1: A
        component_2: B
        foo: int

    class Y(X):
        component_2: C  # type: ignore
        bar: int

    assert A.__depends_on__ == {}
    assert B.__depends_on__ == {}
    assert C.__depends_on__ == {}
    assert X.__depends_on__ == {"component_1": A, "component_2": B}
    assert Y.__depends_on__ == {"component_1": A, "component_2": C}


def test_repr():
    class A(Component):
        pass

    a = A(config={}, logger=None, loop=None)
    assert repr(a) == "<tests.test_component.A()>"


@pytest.mark.asyncio
async def test_setup_and_shutdown(event_loop):
    setup_log = []
    shutdown_log = []

    class A(Component):
        async def on_setup(self):
            setup_log.append("a")

        async def on_shutdown(self):
            shutdown_log.append("a")

    class B(Component):
        a: A

        async def on_setup(self):
            setup_log.append("b")

        async def on_shutdown(self):
            shutdown_log.append("b")

    class C(Component):
        a: A

        async def on_setup(self):
            setup_log.append("c")

        async def on_shutdown(self):
            shutdown_log.append("c")

    class D(Component):
        b: B
        c: C

        async def on_setup(self):
            setup_log.append("d")

        async def on_shutdown(self):
            shutdown_log.append("d")

    logger = logging.getLogger(__name__)

    a = A(config={}, logger=logger, loop=event_loop)
    b = B(config={}, logger=logger, loop=event_loop)
    c = C(config={}, logger=logger, loop=event_loop)
    d = D(config={}, logger=logger, loop=event_loop)

    assert not a.active.is_set()
    assert a.released.is_set()
    assert a.depends_on == set()
    assert a.required_by == set()

    assert not b.active.is_set()
    assert b.released.is_set()
    assert b.depends_on == set()
    assert b.required_by == set()

    assert not c.active.is_set()
    assert c.released.is_set()
    assert c.depends_on == set()
    assert c.required_by == set()

    assert not d.active.is_set()
    assert d.released.is_set()
    assert d.depends_on == set()
    assert d.required_by == set()

    await asyncio.gather(a.setup(), b.setup(a=a), c.setup(a=a), d.setup(b=b, c=c))
    assert setup_log in (["a", "b", "c", "d"], ["a", "c", "b", "d"])

    assert a.active.is_set()
    assert not a.released.is_set()
    assert a.depends_on == set()
    assert a.required_by == {b, c}

    assert b.active.is_set()
    assert not b.released.is_set()
    assert b.depends_on == {a}
    assert b.required_by == {d}
    assert b.a is a

    assert c.active.is_set()
    assert not c.released.is_set()
    assert c.depends_on == {a}
    assert c.required_by == {d}
    assert c.a is a

    assert d.active.is_set()
    assert d.released.is_set()
    assert d.depends_on == {b, c}
    assert d.required_by == set()
    assert d.b is b
    assert d.c is c

    await asyncio.gather(a.shutdown(), b.shutdown(), c.shutdown(), d.shutdown())
    assert shutdown_log in (["d", "b", "c", "a"], ["d", "c", "b", "a"])

    assert not a.active.is_set()
    assert a.released.is_set()
    assert a.depends_on == set()
    assert a.required_by == set()

    assert not b.active.is_set()
    assert b.released.is_set()
    assert b.depends_on == set()
    assert b.required_by == set()

    assert not c.active.is_set()
    assert c.released.is_set()
    assert c.depends_on == set()
    assert c.required_by == set()

    assert not d.active.is_set()
    assert d.released.is_set()
    assert d.depends_on == set()
    assert d.required_by == set()

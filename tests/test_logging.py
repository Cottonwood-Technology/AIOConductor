from logging import getLogger

from aioconductor import (
    Conductor,
    Component,
    SimpleLoggingPolicy,
    ModuleLoggingPolicy,
    ComponentLoggingPolicy,
)


class A(Component):
    pass


class B(Component):
    pass


def test_simple_logging_policy() -> None:
    conductor = Conductor(logging_policy=SimpleLoggingPolicy(logger=getLogger("test")))

    a = conductor.add(A)
    b = conductor.add(B)

    assert a.logger.name == "test"
    assert b.logger.name == "test"


def test_module_logging_policy() -> None:
    conductor = Conductor(logging_policy=ModuleLoggingPolicy())

    a = conductor.add(A)
    b = conductor.add(B)

    assert a.logger.name == "tests.test_logging"
    assert b.logger.name == "tests.test_logging"


def test_component_logging_policy() -> None:
    conductor = Conductor(logging_policy=ComponentLoggingPolicy())

    a = conductor.add(A)
    b = conductor.add(B)

    assert a.logger.name == "tests.test_logging.a"
    assert b.logger.name == "tests.test_logging.b"

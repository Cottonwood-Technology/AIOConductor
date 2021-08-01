from aioconductor import Conductor, Component, Config, SimpleConfigPolicy


class A(Component):
    pass


class B(Component):
    pass


def test_simple_config_policy() -> None:
    config: Config = {}
    conductor = Conductor(config_policy=SimpleConfigPolicy(config=config))

    a = conductor.add(A)
    b = conductor.add(B)

    assert a.config is config
    assert b.config is config

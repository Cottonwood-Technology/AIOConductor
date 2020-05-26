
AIOConductor
============

It is a small library,
which solves single task:
orchestration of asynchronous applications.

For example,
we have an application,
which consists of database,
message queue,
web API,
and background workers.
Database and message queue are independent,
they can be launched concurrently.
Web API and background workers are independent too.
But they both depend on database and message queue.
So they should be launched after and stopped before database and message queue.

This is how it can be solved using AIOConductor.

..  code-block:: python

    from aioconductor import Conductor, Component

    class Database(Component):

        async def on_setup(self):
            """ Setup database """

        async def on_shutdown(self):
            """ Shutdown database """

    class MessageQueue(Component):

        async def on_setup(self):
            """ Setup message queue """

        async def on_shutdown(self):
            """ Shutdown message queue """

    class WebAPI(Component):

        db: Database         # Dependencies are declared by type annotations.
        queue: MessageQueue  # Real instances of the components will be injected
                             # during setup routine.

        async def on_setup(self):
            """ Setup web API """

        async def on_shutdown(self):
            """ Shutdown web API """

    class BackgroundWorkers(Component):

        db: Database
        queue: MessageQueue

        async def on_setup(self):
            """ Setup background workers """

        async def on_shutdown(self):
            """ Shutdown background workers """

    conductor = Conductor(config={})
    conductor.add(WebAPI)
    conductor.add(BackgroundWorkers)
    conductor.serve()

The code above will run concurrent setup of ``Database`` and ``MessageQueue``,
and then concurrent setup of ``WebAPI`` and ``BackgroundWorkers``.
Shutdown will be run in opposite order.

Conductor also provides ability to patch component by alternative implementation.
It can be useful for testing.

..  code-block:: python

    class MessageQueueMock(Component):
        async def on_setup(self):
            """ Setup message queue mock """

        async def on_shutdown(self):
            """ Shutdown message queue mock """

    conductor = Conductor(config={})

    conductor.patch(MessageQueue, MessageQueueMock)
    # An instance of ``MessageQueueMock`` will be injected into
    # ``WebAPI`` and ``BackgroundWorkers``, instead of ``MessageQueue``.

    conductor.add(WebAPI)
    conductor.add(BackgroundWorkers)
    conductor.serve()

"""
Process communication example

Covers:

- Resources: Store

Scenario:
  This example shows how to interconnect simulation model elements
  together using :class:`~simcy.resources.store.Store` for one-to-one,
  and many-to-one asynchronous processes. For one-to-many a simple
  BroadCastPipe class is constructed from Store.

When Useful:
  When a consumer process does not always wait on a generating process
  and these processes run asynchronously. This example shows how to
  create a buffer and also tell is the consumer process was late
  yielding to the event from a generating process.

  This is also useful when some information needs to be broadcast to
  many receiving processes

  Finally, using pipes can simplify how processes are interconnected to
  each other in a simulation model.

Example By:
  Keith Smith

"""
import random
from time import perf_counter_ns


RANDOM_SEED = 42
SIM_TIME = 100


log = ""


class BroadcastPipe(object):
    """A Broadcast pipe that allows one process to send messages to many.

    This construct is useful when message consumers are running at
    different rates than message generators and provides an event
    buffering to the consuming processes.

    The parameters are used to create a new
    :class:`~simcy.resources.store.Store` instance each time
    :meth:`get_output_conn()` is called.

    """
    def __init__(self, env, capacity, des):
        self.env = env
        self.capacity = capacity
        self.pipes = []
        self.des = des

    def put(self, value):
        """Broadcast a *value* to all receivers."""
        if not self.pipes:
            raise RuntimeError('There are no output pipes.')
        events = [store.put(value) for store in self.pipes]
        return self.env.all_of(events)  # Condition event for all "events"

    def get_output_conn(self):
        """Get a new output connection for this broadcast pipe.

        The return value is a :class:`~simcy.resources.store.Store`.

        """
        pipe = self.des.Store(self.env, capacity=self.capacity)
        self.pipes.append(pipe)
        return pipe


def message_generator(name, env, out_pipe):
    """A process which randomly generates messages."""
    while True:
        # wait for next transmission
        yield env.timeout(random.randint(6, 10))

        # messages are time stamped to later check if the consumer was
        # late getting them.  Note, using event.triggered to do this may
        # result in failure due to FIFO nature of simulation yields.
        # (i.e. if at the same env.now, message_generator puts a message
        # in the pipe first and then message_consumer gets from pipe,
        # the event.triggered will be True in the other order it will be
        # False
        msg = (env.now, '%s says hello at %d' % (name, env.now))
        out_pipe.put(msg)


def message_consumer(name, env, in_pipe):
    """A process which consumes messages."""
    global log
    while True:
        # Get event for message pipe
        msg = yield in_pipe.get()

        if msg[0] < env.now:
            # if message was already put into pipe, then
            # message_consumer was late getting to it. Depending on what
            # is being modeled this, may, or may not have some
            # significance
            log += ('LATE Getting Message: at time %d: %s received message: %s' %
                  (env.now, name, msg[1]))

        else:
            # message_consumer is synchronized with message_generator
            log += ('at time %d: %s received message: %s.' %
                  (env.now, name, msg[1]))

        # Process does some other work, which may result in missing messages
        yield env.timeout(random.randint(4, 8))

def run(des):
    global log
    run_time = 0
    random.seed(RANDOM_SEED)
    env = des.Environment()

    # For one-to-one or many-to-one type pipes, use Store
    pipe = des.Store(env)
    env.process(message_generator('Generator A', env, pipe))
    env.process(message_consumer('Consumer A', env, pipe))

    log += ('\nOne-to-one pipe communication\n')
    start = perf_counter_ns()
    env.run(until=SIM_TIME)
    end = perf_counter_ns()

    run_time += (end - start)

    # For one-to many use BroadcastPipe
    # (Note: could also be used for one-to-one,many-to-one or many-to-many)
    env = des.Environment()
    bc_pipe = BroadcastPipe(env, des.core.Infinity, des)

    env.process(message_generator('Generator A', env, bc_pipe))
    env.process(message_consumer('Consumer A', env, bc_pipe.get_output_conn()))
    env.process(message_consumer('Consumer B', env, bc_pipe.get_output_conn()))

    log += ('\nOne-to-many pipe communication\n')

    start = perf_counter_ns()
    env.run(until=SIM_TIME)
    end = perf_counter_ns()

    run_time += (end - start)

    return run_time, log


"""
Event Latency example

Covers:

- Resources: Store

Scenario:
  This example shows how to separate the time delay of events between
  processes from the processes themselves.

When Useful:
  When modeling physical things such as cables, RF propagation, etc.  it
  better encapsulation to keep this propagation mechanism outside of the
  sending and receiving processes.

  Can also be used to interconnect processes sending messages

Example by:
  Keith Smith

"""
from time import perf_counter_ns

SIM_DURATION = 100


log = ""


class Cable(object):
    """This class represents the propagation through a cable."""
    def __init__(self, env, delay, des):
        self.env = env
        self.delay = delay
        self.store = des.Store(env)

    def latency(self, value):
        yield self.env.timeout(self.delay)
        self.store.put(value)

    def put(self, value):
        self.env.process(self.latency(value))

    def get(self):
        return self.store.get()


def sender(env, cable):
    """A process which randomly generates messages."""
    while True:
        # wait for next transmission
        yield env.timeout(5)
        cable.put('Sender sent this at %d' % env.now)


def receiver(env, cable):
    """A process which consumes messages."""
    global log
    while True:
        # Get event for message pipe
        msg = yield cable.get()
        log += ('Received this at %d while %s' % (env.now, msg))


def run(des):
    global log
    run_time = 0
    env = des.Environment()

    cable = Cable(env, 10, des)
    env.process(sender(env, cable))
    env.process(receiver(env, cable))

    start = perf_counter_ns()
    env.run(until=SIM_DURATION)
    end = perf_counter_ns()
    run_time += (end - start)

    return run_time, log

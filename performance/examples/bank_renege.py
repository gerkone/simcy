"""
Bank renege example

Covers:

- Resources: Resource
- Condition events

Scenario:
  A counter with a random service time and customers who renege. Based on the
  program bank08.py from TheBank tutorial of SimPy 2. (KGM)

"""
import random
from time import perf_counter_ns


RANDOM_SEED = 42
NEW_CUSTOMERS = 5  # Total number of customers
INTERVAL_CUSTOMERS = 10.0  # Generate new customers roughly every x seconds
MIN_PATIENCE = 1  # Min. customer patience
MAX_PATIENCE = 3  # Max. customer patience


def source(env, number, interval, counter):
    """Source generates customers randomly"""
    for i in range(number):
        c = customer(env, 'Customer%02d' % i, counter, time_in_bank=12.0)
        env.process(c)
        t = random.expovariate(1.0 / interval)
        yield env.timeout(t)


def customer(env, name, counter, time_in_bank):
    """Customer arrives, is served and leaves."""
    arrive = env.now

    with counter.request() as req:
        patience = random.uniform(MIN_PATIENCE, MAX_PATIENCE)
        # Wait for the counter or abort at the end of our tether
        results = yield req | env.timeout(patience)

        wait = env.now - arrive

        if req in results:
            tib = random.expovariate(1.0 / time_in_bank)
            yield env.timeout(tib)


def run(des):
    run_time = 0
    random.seed(RANDOM_SEED)
    env = des.Environment()

    # Start processes and run
    counter = des.Resource(env, capacity=1)
    env.process(source(env, NEW_CUSTOMERS, INTERVAL_CUSTOMERS, counter))

    start = perf_counter_ns()
    env.run()
    end = perf_counter_ns()
    run_time += (end - start)

    return run_time


"""
Movie renege example

Covers:

- Resources: Resource
- Condition events
- Shared events

Scenario:
  A movie theatre has one ticket counter selling tickets for three
  movies (next show only). When a movie is sold out, all people waiting
  to buy tickets for that movie renege (leave queue).

"""
import collections
import random
from time import perf_counter_ns


RANDOM_SEED = 42
TICKETS = 50  # Number of tickets per movie
SIM_TIME = 120  # Simulate until


def moviegoer(env, movie, num_tickets, theater):
    """A moviegoer tries to by a number of tickets (*num_tickets*) for
    a certain *movie* in a *theater*.

    If the movie becomes sold out, she leaves the theater. If she gets
    to the counter, she tries to buy a number of tickets. If not enough
    tickets are left, she argues with the teller and leaves.

    If at most one ticket is left after the moviegoer bought her
    tickets, the *sold out* event for this movie is triggered causing
    all remaining moviegoers to leave.

    """
    with theater.counter.request() as my_turn:
        # Wait until its our turn or until the movie is sold out
        result = yield my_turn | theater.sold_out[movie]

        # Check if it's our turn or if movie is sold out
        if my_turn not in result:
            theater.num_renegers[movie] += 1
            return

        # Check if enough tickets left.
        if theater.available[movie] < num_tickets:
            # Moviegoer leaves after some discussion
            yield env.timeout(0.5)
            return

        # Buy tickets
        theater.available[movie] -= num_tickets
        if theater.available[movie] < 2:
            # Trigger the "sold out" event for the movie
            theater.sold_out[movie].succeed()
            theater.when_sold_out[movie] = env.now
            theater.available[movie] = 0
        yield env.timeout(1)


def customer_arrivals(env, theater):
    """Create new *moviegoers* until the sim time reaches 120."""
    while True:
        yield env.timeout(random.expovariate(1 / 0.5))

        movie = random.choice(theater.movies)
        num_tickets = random.randint(1, 6)
        if theater.available[movie]:
            env.process(moviegoer(env, movie, num_tickets, theater))


Theater = collections.namedtuple('Theater', 'counter, movies, available, '
                                            'sold_out, when_sold_out, '
                                            'num_renegers')


def run(des):
    log = ""
    run_time = 0

    random.seed(RANDOM_SEED)
    env = des.Environment()

    # Create movie theater
    counter = des.Resource(env, capacity=1)
    movies = ['Python Unchained', 'Kill Process', 'Pulp Implementation']
    available = {movie: TICKETS for movie in movies}
    sold_out = {movie: env.event() for movie in movies}
    when_sold_out = {movie: None for movie in movies}
    num_renegers = {movie: 0 for movie in movies}
    theater = Theater(counter, movies, available, sold_out, when_sold_out,
                      num_renegers)

    # Start process and run
    env.process(customer_arrivals(env, theater))
    start = perf_counter_ns()
    env.run(until=SIM_TIME)
    end = perf_counter_ns()
    run_time += (end - start)

    # Analysis/results
    for movie in movies:
        if theater.sold_out[movie]:
            log += ('Movie "%s" sold out %.1f minutes after ticket counter '
                  'opening.' % (movie, theater.when_sold_out[movie]))
            log += ('  Number of people leaving queue when film sold out: %s' %
                  theater.num_renegers[movie])

    return run_time, log

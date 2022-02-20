import os
import importlib.util
import simpy
import simcy
import random
import cProfile, pstats
import datetime


if __name__ == "__main__":
    random.seed(0)
    performance_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")

    tests = [f for f in os.listdir(performance_dir) if ".py" in f]

    for des in [simpy, simcy]:
        profiler = cProfile.Profile()
        profiler.enable()

        for test in tests:
            spec = importlib.util.spec_from_file_location("{}.run".format(test.split(".")[0]), os.path.join(performance_dir, test))
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            avg_run_time = 0
            avg_total_parts = 0

            for _ in range(20):
                run_time = test_module.run(des)
                avg_run_time += run_time

            avg_run_time /= 10
            avg_total_parts /= 10

            print("{} - {} - avg run: {:.0f}us".format(str(des.__name__), test, avg_run_time / 1000))

        profiler.disable()

        if not os.path.exists("profiling"):
            os.makedirs("profiling".format(str(des.__name__)))

        stats = pstats.Stats(profiler).sort_stats('ncalls')
        filename = "profiling/{}_prof_{}".format(str(des.__name__), datetime.datetime.timestamp(datetime.datetime.now()))
        stats.dump_stats(filename + ".pstat")
        # --root='core:183:step'
        os.popen(
            "gprof2dot -f pstats {0}.pstat -n 1.0 -e 0.5 --color-nodes-by-selftime | dot -Tpng -o {0}.png".format(filename))

        print("--")

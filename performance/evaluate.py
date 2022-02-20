import os
import importlib.util
import warnings

import simpy
import simcy
import cProfile, pstats
import datetime


def run_and_time(tests):
    logs = {}

    for des in [simpy, simcy]:
        des_name = str(des.__name__)
        logs[des_name] = {}
        profiler = cProfile.Profile()
        profiler.enable()

        for test in tests:
            spec = importlib.util.spec_from_file_location("{}.run".format(test.split(".")[0]),
                                                          os.path.join(performance_dir, test))
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            avg_run_time = 0

            for _ in range(1):
                run_time, log = test_module.run(des)
                avg_run_time += run_time

            avg_run_time /= 10
            logs[des_name][test] = log

            print("{} - {} - avg run: {:.0f}us".format(des_name, test, avg_run_time / 1000))

        profiler.disable()

        if not os.path.exists("profiling"):
            os.makedirs("profiling".format(des_name))

        stats = pstats.Stats(profiler).sort_stats('ncalls')
        filename = "profiling/{}_prof_{}".format(des_name, datetime.datetime.timestamp(datetime.datetime.now()))
        stats.dump_stats(filename + ".pstat")
        # --root='core:183:step'
        os.popen(
            "gprof2dot -f pstats {0}.pstat -n 1.0 -e 0.5 --color-nodes-by-selftime | dot -Tpng -o {0}.png".format(
                filename))

        print("--")

    return logs


def validate(logs, tests):
    for test in tests:
        try:
            assert logs["simpy"][test] == logs["simcy"][test]
            print("{} OK!".format(test))
        except AssertionError:
            warnings.warn("Output mismatch on example {}!\n"
                          "simPY: {}\nsimCY: {}".format(test, logs["simpy"][test], logs["simcy"][test]))


if __name__ == "__main__":
    performance_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")
    tests = [f for f in os.listdir(performance_dir) if ".py" in f]

    logs = run_and_time(tests)
    print("validate")
    validate(logs, tests)



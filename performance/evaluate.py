import os
import importlib.util
import simpy
import simcy
import random

if __name__ == "__main__":
    random.seed(0)
    performance_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples/")

    tests = [f for f in os.listdir(performance_dir) if ".py" in f]

    for test in tests:
        spec = importlib.util.spec_from_file_location("{}.run".format(test.split(".")[0]), os.path.join(performance_dir, test))
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        for des in [simpy, simcy]:
            avg_run_time = 0
            avg_total_parts = 0

            for _ in range(20):
                run_time = test_module.run(des)
                avg_run_time += run_time

            avg_run_time /= 10
            avg_total_parts /= 10

            print("{} - {} - avg run: {:.0f}us".format(test, str(des.__name__), avg_run_time / 1000))

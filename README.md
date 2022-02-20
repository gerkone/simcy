# simcy
Cythonized [SimPy](https://gitlab.com/team-simpy/simpy) fork.

I like how simpy is structured and the usage of `yield` statements for events, but I found that simpy was
too slow for big simulations.

There is also a similar [project](https://github.com/chaosmail/simpy-cython), but it's very outdated and simpy has been updated since.

## Install
First install the requirements
```
pip install -r requirements.txt
```
Then build the cython extensions and install `simcy` as a package
```
python setup.py build_ext --inplace
pip install .
```

## Current state
The current progress is only a partial conversion to cython. This is because `yield` statements have issues and do not
really work with cython. As a consequence if the `Events` get cythonized blindly the processes are not executed anymore.

Some files are still in pure python (`store.py` and `container.py`).

## Results (up to now)
There is some (more or less consistent) __simulation__ performance improvement.

Performance tests can be found [here](performance/) (manual) and [here](tests/test_benchmark.py) (pytest).

### Examples
The results are averaged over 20 runs. To rerun the evaluation simply execute the [performace/evaluate.py](performance/evaluate.py)  script, which will 
automatically execute and time all examples (both `simpy` and `simcy` need to be installed for that)

#### Machine shop
```
simpy - avg run: 292289us
simcy - avg run: 210112us
```

#### Latency
```
simpy - avg run: 697us
simcy - avg run: 438us
```

#### Movie renege
```
simpy - avg run: 5011us
simcy - avg run: 3668us
```

#### Carwash
```
simpy - avg run: 342us
simcy - avg run: 257us
```


### pytest benchmark
Functions that end with `_py` are with simpy, rest is with simcy.
```
----------------------------------------------------------------------------------- benchmark 'simulation': 6 tests ------------------------------------------------------------------------------------
Name (time in us)              Min                   Max                Mean              StdDev              Median                 IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_store_sim            159.1000 (1.0)      1,151.7960 (1.28)     180.2665 (1.0)       38.8776 (1.03)     171.9920 (1.0)       10.1068 (1.16)      337;395        5.5473 (1.0)        3933           1
test_resource_sim         182.6200 (1.15)       911.4550 (1.01)     214.2840 (1.19)      53.7990 (1.42)     197.8340 (1.15)      12.6130 (1.45)      398;475        4.6667 (0.84)       3820           1
test_container_sim        193.9210 (1.22)       898.7370 (1.0)      218.4881 (1.21)      37.8621 (1.0)      209.5015 (1.22)       8.7135 (1.0)       331;380        4.5769 (0.83)       4232           1
test_store_sim_py         247.8640 (1.56)     3,868.6250 (4.30)     282.5478 (1.57)     101.3703 (2.68)     264.0800 (1.54)      11.4927 (1.32)      122;524        3.5392 (0.64)       3037           1
test_container_sim_py     305.7810 (1.92)     2,693.4730 (3.00)     515.1926 (2.86)     238.4062 (6.30)     436.7995 (2.54)     254.8880 (29.25)     425;150        1.9410 (0.35)       2820           1
test_resource_sim_py      322.1250 (2.02)     1,262.7430 (1.41)     364.3718 (2.02)      73.4432 (1.94)     337.1565 (1.96)      16.7130 (1.92)      199;306        2.7444 (0.49)       1566           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```

```
------------------------------------------------------------------------------------- benchmark 'targeted': 6 tests -------------------------------------------------------------------------------------
Name (time in us)                 Min                   Max                Mean             StdDev              Median                IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_condition_wait          182.6430 (1.0)        660.5340 (1.0)      197.1043 (1.0)      30.4741 (1.0)      193.7305 (1.0)      12.1760 (1.88)      172;204        5.0735 (1.0)        4448           1
test_condition_events        213.2160 (1.17)     1,069.1920 (1.62)     258.9522 (1.31)     78.3962 (2.57)     235.7070 (1.22)     17.6215 (2.72)      159;212        3.8617 (0.76)       1280           1
test_wait_for_proc           226.4230 (1.24)       831.3080 (1.26)     248.3921 (1.26)     40.9482 (1.34)     239.2340 (1.23)     16.4593 (2.54)      172;198        4.0259 (0.79)       3397           1
test_condition_wait_py       290.3110 (1.59)       843.4380 (1.28)     321.8150 (1.63)     50.3690 (1.65)     308.3610 (1.59)      6.4700 (1.0)       159;553        3.1074 (0.61)       1973           1
test_wait_for_proc_py        330.6620 (1.81)       985.3190 (1.49)     357.7853 (1.82)     48.2099 (1.58)     343.2100 (1.77)     10.6643 (1.65)      220;391        2.7950 (0.55)       2641           1
test_condition_events_py     353.1270 (1.93)       808.9580 (1.22)     386.9436 (1.96)     56.6151 (1.86)     370.8635 (1.91)     10.7000 (1.65)       83;126        2.5844 (0.51)        842           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```